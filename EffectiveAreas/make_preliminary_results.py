#!/usr/bin/env python3
"""Generate primary neutrino interactions, validate them, and save simple plots.

Run with the project's interpreter:
    .venv/bin/python EffectiveAreas/make_preliminary_results.py

The default CTW sample works offline. No detector simulation or PROPOSAL is
required. The separate radio example is an Alvarez2009 parametrization in
homogeneous ice, not a signal propagated through the RNO-G detector.
"""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache" / "matplotlib"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import h5py
import numpy as np

from NuRadioMC.EvtGen.generator import generate_eventlist_cylinder
from NuRadioMC.utilities import cross_sections
from NuRadioReco.utilities import units


FLAVOURS = np.array([12, -12, 14, -14, 16, -16])
LABELS = [r"$\nu_e$", r"$\bar\nu_e$", r"$\nu_\mu$", r"$\bar\nu_\mu$",
          r"$\nu_\tau$", r"$\bar\nu_\tau$"]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--events", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--log-energy-min", type=float, default=16)
    parser.add_argument("--log-energy-max", type=float, default=20)
    parser.add_argument("--radius-km", type=float, default=5)
    parser.add_argument("--depth-km", type=float, default=3)
    parser.add_argument("--model", choices=["ctw", "hedis_bgr18"], default="ctw",
                        help="BGR18 may download a cross-section table on first use")
    parser.add_argument("--output", type=Path, default=HERE / "preliminary_results")
    parser.add_argument("--input", type=Path, help="Plot an existing primary-only generator HDF5")
    parser.add_argument("--regenerate", action="store_true",
                        help="Replace this run's generated HDF5 if it already exists")
    parser.add_argument("--skip-radio-example", action="store_true")
    args = parser.parse_args()
    if args.events < 1 or args.radius_km <= 0 or args.depth_km <= 0:
        parser.error("events, radius and depth must be positive")
    if args.log_energy_max < args.log_energy_min:
        parser.error("maximum energy must not be below minimum energy")
    args.output = args.output.expanduser().resolve()
    return args


def get_input(args):
    if args.input:
        return args.input.expanduser().resolve()
    path = args.output / "neutrino_events.hdf5"
    settings = {
        "events": args.events, "seed": args.seed, "model": args.model,
        "log_energy_min": args.log_energy_min, "log_energy_max": args.log_energy_max,
        "radius_km": args.radius_km, "depth_km": args.depth_km,
    }
    signature = json.dumps(settings, sort_keys=True)
    if path.exists() and not args.regenerate:
        with h5py.File(path, "r") as f:
            if f.attrs.get("preliminary_settings", "") != signature:
                raise ValueError("Existing sample has different settings. Choose another --output "
                                 "or explicitly use --regenerate.")
        print(f"Reusing {path}", flush=True)
        return path
    print(f"Generating {args.events:,} primary neutrinos ({args.model})...", flush=True)
    generate_eventlist_cylinder(
        str(path), n_events=args.events,
        Emin=10.0 ** args.log_energy_min * units.eV,
        Emax=10.0 ** args.log_energy_max * units.eV,
        volume={"fiducial_rmin": 0 * units.km,
                "fiducial_rmax": args.radius_km * units.km,
                "fiducial_zmin": -args.depth_km * units.km,
                "fiducial_zmax": 0 * units.km},
        thetamin=0 * units.deg, thetamax=180 * units.deg,
        phimin=0 * units.deg, phimax=360 * units.deg,
        flavor=FLAVOURS.tolist(), spectrum="log_uniform", deposited=False,
        proposal=False, seed=args.seed, interaction_type="ccnc",
        cross_sections_model=args.model,
    )
    with h5py.File(path, "a") as f:
        f.attrs["preliminary_settings"] = signature
        f.attrs["preliminary_cross_sections_model"] = args.model
        f.attrs["preliminary_seed"] = args.seed
    return path


def read_input(path):
    keys = ["event_group_ids", "energies", "flavors", "interaction_type", "inelasticity",
            "zeniths", "azimuths", "xx", "yy", "zz", "shower_energies", "shower_type"]
    with h5py.File(path, "r") as f:
        missing = set(keys) - set(f.keys())
        if missing:
            raise ValueError(f"Missing generator datasets: {sorted(missing)}")
        data = {key: f[key][:] for key in keys}
        attrs = dict(f.attrs)
        if "n_interaction" in f and np.any(f["n_interaction"][:] != 1):
            raise ValueError("This diagnostic expects primary-only samples (proposal=False).")
    for key in ["interaction_type", "shower_type"]:
        data[key] = np.char.lower(data[key].astype(str))
    _, first, counts = np.unique(data["event_group_ids"], return_index=True, return_counts=True)
    primary = {key: value[first] for key, value in data.items()}
    primary["n_showers"] = counts
    return data, primary, attrs


def energy_edges(energies, bins=32):
    low, high = np.log10(energies.min()), np.log10(energies.max())
    if np.isclose(low, high):
        low, high = low - 0.25, high + 0.25
    return np.logspace(low, high, bins + 1)


def git_revision():
    import NuRadioMC
    try:
        result = subprocess.run(["git", "-C", str(Path(NuRadioMC.__file__).parent),
                                 "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate(data, p, attrs):
    n = len(p["energies"])
    electron_cc = (np.abs(p["flavors"]) == 12) & (p["interaction_type"] == "cc")
    had = data["shower_type"] == "had"
    em = data["shower_type"] == "em"
    checks = {
        "primary_count_matches_metadata": n == int(attrs["n_events"]),
        "only_cc_nc": bool(np.isin(p["interaction_type"], ["cc", "nc"]).all()),
        "physical_inelasticities": bool(((p["inelasticity"] >= 0) &
                                        (p["inelasticity"] <= 1)).all()),
        "primary_energy_bounds": bool(((p["energies"] >= attrs["Emin"]) &
                                       (p["energies"] <= attrs["Emax"])).all()),
        "zenith_bounds": bool(((p["zeniths"] >= attrs["thetamin"]) &
                               (p["zeniths"] <= attrs["thetamax"])).all()),
        "azimuth_bounds": bool(((p["azimuths"] >= attrs["phimin"]) &
                                (p["azimuths"] <= attrs["phimax"])).all()),
        "one_hadronic_shower_per_primary": int(had.sum()) == n,
        "electromagnetic_count_matches_electron_cc": int(em.sum()) == int(electron_cc.sum()),
        "multiplicity_matches_interaction": bool(np.array_equal(
            p["n_showers"], 1 + electron_cc.astype(int))),
        "hadronic_energy_partition": bool(np.allclose(
            data["shower_energies"][had],
            data["energies"][had] * data["inelasticity"][had], rtol=1e-10, atol=0)),
        "electromagnetic_energy_partition": bool(np.allclose(
            data["shower_energies"][em],
            data["energies"][em] * (1 - data["inelasticity"][em]), rtol=1e-10, atol=0)),
    }
    if "fiducial_rmax" in attrs:
        r = np.hypot(p["xx"] - attrs.get("x0", 0), p["yy"] - attrs.get("y0", 0))
        checks["vertices_inside_volume"] = bool(
            (r >= attrs.get("fiducial_rmin", 0)).all() and
            (r <= attrs["fiducial_rmax"]).all() and
            (p["zz"] >= attrs["fiducial_zmin"]).all() and
            (p["zz"] <= attrs["fiducial_zmax"]).all())
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"Physical/data consistency checks failed: {failed}")
    return checks


def draw_energy(ax, p):
    energies = p["energies"] / units.eV
    ax.hist(energies, bins=energy_edges(energies), histtype="step", linewidth=1.5)
    ax.set(xscale="log", xlabel=r"$E_\nu$ [eV]", ylabel="Neutrinos / bin")


def draw_y(ax, p):
    for current, color in [("cc", "C0"), ("nc", "C1")]:
        mask = p["interaction_type"] == current
        if mask.any():
            ax.hist(p["inelasticity"][mask], bins=np.linspace(0, 1, 41), density=True,
                    histtype="step", linewidth=1.5, color=color, label=current.upper())
    ax.set(xlabel=r"Inelasticity $y$", ylabel="Probability density", xlim=(0, 1))
    ax.legend()


def draw_flavours(ax, p):
    counts = [np.count_nonzero(p["flavors"] == flavour) for flavour in FLAVOURS]
    ax.bar(np.arange(6), counts, width=0.65)
    ax.set(xticks=np.arange(6), xticklabels=LABELS, ylabel="Primary neutrinos")


def draw_cosine(ax, p, attrs):
    low, high = np.cos(attrs["thetamax"]), np.cos(attrs["thetamin"])
    ax.hist(np.cos(p["zeniths"]), bins=np.linspace(low, high, 31), density=True,
            histtype="step", linewidth=1.5)
    ax.axhline(1 / (high - low), color="0.3", linestyle="--", linewidth=1,
               label="Uniform sampling")
    ax.set(xlabel=r"$\cos\theta$", ylabel="Probability density", xlim=(low, high))
    ax.legend()


def draw_azimuth(ax, p, attrs):
    low, high = np.rad2deg([attrs["phimin"], attrs["phimax"]])
    ax.hist(np.rad2deg(p["azimuths"]), bins=np.linspace(low, high, 31), density=True,
            histtype="step", linewidth=1.5)
    ax.axhline(1 / (high - low), color="0.3", linestyle="--", linewidth=1)
    ax.set(xlabel=r"Azimuth $\phi$ [deg]", ylabel=r"Probability density [deg$^{-1}$]",
           xlim=(low, high))


def draw_current_counts(ax, p):
    counts = [np.count_nonzero(p["interaction_type"] == current) for current in ["cc", "nc"]]
    ax.bar(["CC", "NC"], counts, color=["C0", "C1"], width=0.55)
    ax.set(ylabel="Primary interactions")


def make_figures(data, p, attrs, model, output, radio):
    plt.rcdefaults()
    plt.rcParams.update({"font.size": 11, "savefig.dpi": 180})
    directory = output / "figures"
    directory.mkdir(exist_ok=True)
    saved = []

    def save(fig, name):
        fig.savefig(directory / f"{name}.png")
        fig.savefig(directory / f"{name}.svg")
        saved.append(name)
        plt.close(fig)
        print(f"  Figure: {name}", flush=True)

    fig, ax = plt.subplots(figsize=(6.4, 4.3), layout="constrained")
    draw_energy(ax, p)
    save(fig, "01_neutrino_energy")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout="constrained")
    lo, hi = np.rad2deg([attrs["thetamin"], attrs["thetamax"]])
    axes[0].hist(np.rad2deg(p["zeniths"]), bins=np.linspace(lo, hi, 31), density=True,
                 histtype="step", linewidth=1.5)
    theta = np.linspace(attrs["thetamin"], attrs["thetamax"], 200)
    axes[0].plot(np.rad2deg(theta), np.sin(theta) * np.pi / 180 /
                 (np.cos(attrs["thetamin"]) - np.cos(attrs["thetamax"])),
                 "--", color="0.3", linewidth=1, label="Isotropic sampling")
    axes[0].set(xlabel=r"Zenith $\theta$ [deg]", ylabel=r"Probability density [deg$^{-1}$]")
    axes[0].legend(fontsize=9)
    draw_cosine(axes[1], p, attrs)
    draw_azimuth(axes[2], p, attrs)
    save(fig, "02_arrival_directions")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout="constrained")
    artist = axes[0].hexbin(p["xx"] / units.km, p["yy"] / units.km,
                            gridsize=35, mincnt=1, rasterized=True)
    axes[0].set(xlabel="x [km]", ylabel="y [km]", aspect="equal")
    fig.colorbar(artist, ax=axes[0], label="Neutrinos", shrink=0.85)
    axes[1].hist(p["zz"] / units.km, bins=30, density=True, histtype="step", linewidth=1.5)
    axes[1].set(xlabel="z [km]", ylabel=r"Probability density [km$^{-1}$]")
    radius = np.hypot(p["xx"] - attrs.get("x0", 0), p["yy"] - attrs.get("y0", 0)) / units.km
    axes[2].hist(radius, bins=30, density=True, histtype="step", linewidth=1.5)
    if "fiducial_rmax" in attrs:
        rmin, rmax = attrs.get("fiducial_rmin", 0) / units.km, attrs["fiducial_rmax"] / units.km
        rr = np.linspace(rmin, rmax, 100)
        axes[2].plot(rr, 2 * rr / (rmax ** 2 - rmin ** 2), "--", color="0.3",
                     linewidth=1, label="Uniform volume")
        axes[2].legend(fontsize=9)
    axes[2].set(xlabel="r [km]", ylabel=r"Probability density [km$^{-1}$]")
    save(fig, "03_interaction_vertices")

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout="constrained")
    draw_flavours(axes[0], p)
    cc_fractions = []
    for flavour in FLAVOURS:
        mask = p["flavors"] == flavour
        cc_fractions.append(np.mean(p["interaction_type"][mask] == "cc") if mask.any() else np.nan)
    cc_fractions = np.asarray(cc_fractions)
    axes[1].bar(np.arange(6), cc_fractions, label="CC", width=0.65)
    axes[1].bar(np.arange(6), 1 - cc_fractions, bottom=cc_fractions, label="NC", width=0.65)
    axes[1].set(xticks=np.arange(6), xticklabels=LABELS, ylim=(0, 1), ylabel="Interaction fraction")
    axes[1].legend(loc="lower right")
    save(fig, "04_flavours_and_interactions")

    fig, ax = plt.subplots(figsize=(6.4, 4.3), layout="constrained")
    draw_y(ax, p)
    save(fig, "05_inelasticity")

    fig, ax = plt.subplots(figsize=(6.4, 4.3), layout="constrained")
    edges = energy_edges(p["energies"] / units.eV, bins=10)
    for sign, flavour, label, color in [(1, 12, r"$\nu$", "C0"),
                                        (-1, -12, r"$\bar\nu$", "C1")]:
        means, fractions, errors = [], [], []
        for bin_index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
            upper = p["energies"] / units.eV <= high if bin_index == len(edges) - 2 else p["energies"] / units.eV < high
            mask = ((np.sign(p["flavors"]) == sign) &
                    (p["energies"] / units.eV >= low) &
                    upper)
            if not mask.any():
                continue
            fraction = np.mean(p["interaction_type"][mask] == "cc")
            means.append(np.exp(np.mean(np.log(p["energies"][mask] / units.eV))))
            fractions.append(fraction)
            errors.append(np.sqrt(fraction * (1 - fraction) / mask.sum()))
        ax.errorbar(means, fractions, yerr=errors, fmt="o", markersize=4,
                    capsize=2, color=color, label=label + " generated")
        if model:
            energy = np.geomspace(edges[0], edges[-1], 200) * units.eV
            cc = cross_sections.get_nu_cross_section(energy, flavors=flavour, inttype="cc",
                                                    cross_section_type=model)
            nc = cross_sections.get_nu_cross_section(energy, flavors=flavour, inttype="nc",
                                                    cross_section_type=model)
            ax.plot(energy / units.eV, cc / (cc + nc), "--", color=color,
                    label=label + " model")
    ax.set(xscale="log", xlabel=r"$E_\nu$ [eV]", ylabel="CC fraction", ylim=(0, 1))
    ax.legend(fontsize=9, ncol=2)
    save(fig, "06_cc_fraction")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    energies = data["shower_energies"] / units.eV
    edges = energy_edges(energies[energies > 0], bins=45)
    for shower_type, label, color in [("had", "Hadronic", "C0"), ("em", "Electromagnetic", "C1")]:
        mask = data["shower_type"] == shower_type
        if mask.any():
            axes[0].hist(energies[mask], bins=edges, histtype="step", linewidth=1.5,
                         label=label, color=color)
    axes[0].set(xscale="log", xlabel=r"$E_{\rm shower}$ [eV]", ylabel="Showers / bin")
    axes[0].legend(fontsize=9)
    values, counts = np.unique(p["n_showers"], return_counts=True)
    axes[1].bar(values, counts, width=0.55)
    axes[1].set(xticks=values, xlabel="Showers per primary neutrino", ylabel="Primary neutrinos")
    save(fig, "07_shower_energies_and_multiplicity")

    radio_info = None
    if radio:
        radio_info = radio_example(save, output)

    fig, axes = plt.subplots(2, 3, figsize=(13, 7.4), layout="constrained")
    draw_energy(axes[0, 0], p)
    draw_cosine(axes[0, 1], p, attrs)
    draw_azimuth(axes[0, 2], p, attrs)
    draw_flavours(axes[1, 0], p)
    draw_current_counts(axes[1, 1], p)
    draw_y(axes[1, 2], p)
    save(fig, "00_overview")
    return saved, radio_info


def radio_example(save, output):
    from NuRadioMC.SignalGen import askaryan
    n_samples, dt = 4096, 0.1 * units.ns
    n_index = 1.78
    theta_c = np.arccos(1 / n_index)
    times = (np.arange(n_samples) - n_samples / 2) * dt / units.ns
    frequencies = np.fft.rfftfreq(n_samples, d=dt / units.s) / 1e6
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    traces, spectra = [], []
    offsets = [0, 1, 2]
    for offset in offsets:
        trace = askaryan.get_time_trace(
            energy=1e18 * units.eV, theta=theta_c + offset * units.deg,
            N=n_samples, dt=dt, shower_type="HAD", n_index=n_index,
            R=1 * units.km, model="Alvarez2009", seed=12345)
        traces.append(trace)
        spectra.append(np.abs(np.fft.rfft(trace)))
    norm = max(spectra[0])
    for offset, trace, spectrum in zip(offsets, traces, spectra):
        label = rf"$\theta-\theta_C={offset}^\circ$"
        axes[0].plot(times, trace / (units.mV / units.m), label=label)
        axes[1].plot(frequencies, spectrum / norm, label=label)
    axes[0].set(xlabel="Time [ns]", ylabel=r"Electric field [mV m$^{-1}$]", xlim=(-6, 6))
    axes[1].set(xlabel="Frequency [MHz]", ylabel="Relative Fourier amplitude", xlim=(0, 1000))
    axes[0].legend(fontsize=9)
    save(fig, "08_askaryan_example")
    np.savetxt(output / "radio_example.csv", np.column_stack([times, *traces]), delimiter=",",
               header="time_ns,field_offset0_V_per_m,field_offset1_V_per_m,field_offset2_V_per_m",
               comments="")
    return {"model": "Alvarez2009", "shower_type": "hadronic", "energy_eV": 1e18,
            "distance_m": 1000, "refractive_index": n_index,
            "viewing_offsets_deg": offsets, "cherenkov_angle_deg": float(np.rad2deg(theta_c)),
            "interpretation": "Separate illustrative shower in homogeneous ice. No ice attenuation, "
                              "firn ray tracing, antenna response, noise or trigger is applied."}


def write_summary(data, p, attrs, path, args, checks, figures, radio_info, elapsed):
    n = len(p["energies"])
    ncc = int(np.count_nonzero(p["interaction_type"] == "cc"))
    em = int(np.count_nonzero(data["shower_type"] == "em"))
    model = attrs.get("preliminary_cross_sections_model", None)
    summary = {
        "input_file": str(path), "python": sys.version.split()[0],
        "architecture": platform.machine(), "nuradiomc_version": importlib.metadata.version("NuRadioMC"),
        "nuradiomc_commit": git_revision(),
        "cross_sections_model": model or "not recorded in input file",
        "seed": int(attrs["preliminary_seed"]) if "preliminary_seed" in attrs else None,
        "generation_settings": json.loads(attrs["preliminary_settings"])
                               if "preliminary_settings" in attrs else None,
        "zenith_bounds_deg": np.rad2deg([attrs["thetamin"], attrs["thetamax"]]).tolist(),
        "azimuth_bounds_deg": np.rad2deg([attrs["phimin"], attrs["phimax"]]).tolist(),
        "n_primary_neutrinos": n, "n_shower_rows": len(data["energies"]),
        "n_cc": ncc, "n_nc": n - ncc, "cc_fraction": ncc / n,
        "n_hadronic_showers": int(np.count_nonzero(data["shower_type"] == "had")),
        "n_electromagnetic_showers": em,
        "energy_min_eV": float(attrs["Emin"] / units.eV),
        "energy_max_eV": float(attrs["Emax"] / units.eV),
        "volume_km3": float(attrs["volume"] / units.km ** 3),
        "mean_inelasticity": float(np.mean(p["inelasticity"])),
        "flavour_counts": {str(int(f)): int(np.count_nonzero(p["flavors"] == f)) for f in FLAVOURS},
        "checks": checks, "figures": figures, "radio_example": radio_info,
        "elapsed_seconds": round(elapsed, 2),
        "scope": "Unweighted forced primary interactions. Sampling distributions, not detected "
                 "events or an astrophysical rate. No Earth absorption or detector response.",
        "inelasticity_note": "CTW uses an energy-independent inelasticity distribution." if model == "ctw"
                             else "See the selected NuRadioMC generator model.",
        "secondary_lepton_propagation": False,
    }
    if model:
        cc = cross_sections.get_nu_cross_section(p["energies"], flavors=p["flavors"],
                                                inttype="cc", cross_section_type=model)
        nc = cross_sections.get_nu_cross_section(p["energies"], flavors=p["flavors"],
                                                inttype="nc", cross_section_type=model)
        probability = cc / (cc + nc)
        comparison = {}
        for sign, name in [(1, "neutrinos"), (-1, "antineutrinos")]:
            selected = np.sign(p["flavors"]) == sign
            expected = float(probability[selected].sum())
            observed = int(np.count_nonzero(p["interaction_type"][selected] == "cc"))
            variance = float(np.sum(probability[selected] * (1 - probability[selected])))
            comparison[name] = {"expected_cc_count": expected, "observed_cc_count": observed,
                                "mc_standard_deviation": float(np.sqrt(variance)),
                                "pull": float((observed - expected) / np.sqrt(variance)) if variance > 0 else None}
        summary["cc_model_comparison"] = comparison
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (args.output / "interaction_counts.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["pdg_flavour", "primary_count", "cc_count", "nc_count", "mean_inelasticity"])
        for flavour in FLAVOURS:
            mask = p["flavors"] == flavour
            cc = int(np.count_nonzero(p["interaction_type"][mask] == "cc"))
            writer.writerow([flavour, int(mask.sum()), cc, int(mask.sum()) - cc,
                             float(np.mean(p["inelasticity"][mask])) if mask.any() else ""])
    rows = "\n".join(f"| {int(f)} | {summary['flavour_counts'][str(int(f))]:,} |" for f in FLAVOURS)
    figures_md = "\n".join(f"- [{name}](figures/{name}.png)" for name in figures)
    report = f"""# Résultats préliminaires

## Configuration

- NuRadioMC : {summary['nuradiomc_version']}, commit `{summary['nuradiomc_commit']}`.
- Modèle des interactions : `{summary['cross_sections_model']}` ; seed : {summary['seed']}.
- {n:,} neutrinos primaires, {len(data['energies']):,} lignes de showers.
- Énergie primaire : {summary['energy_min_eV']:.2e} à {summary['energy_max_eV']:.2e} eV.
- Volume de génération : {summary['volume_km3']:.2f} km³.
- Directions échantillonnées uniformément en cos(zenith) et en azimut dans les bornes du fichier.
- Interactions primaires uniquement, sans propagation des muons et des taus.

Il s'agit d'interactions forcées non pondérées dans le volume : les histogrammes
décrivent l'échantillonnage et la physique du générateur. Ils ne représentent pas
une population détectée, une aire effective ou un taux astrophysique. L'absorption
dans la Terre et la réponse de RNO-G restent à simuler.

Avec le choix CTW par défaut, la distribution d'inélasticité est indépendante de
l'énergie. Le modèle et ses hypothèses sont conservés ici explicitement pour
ce premier contrôle reproductible et utilisable hors ligne.

## Comptages

| Quantité | Valeur |
| --- | ---: |
| Neutrinos primaires | {n:,} |
| Interactions CC | {ncc:,} ({100*ncc/n:.2f} %) |
| Interactions NC | {n-ncc:,} ({100*(n-ncc)/n:.2f} %) |
| Showers hadroniques | {summary['n_hadronic_showers']:,} |
| Showers électromagnétiques | {em:,} |
| Inélasticité moyenne | {summary['mean_inelasticity']:.4f} |

| Saveur PDG | Neutrinos primaires |
| --- | ---: |
{rows}

Un neutrino électronique en interaction CC produit deux showers : hadronique et
électromagnétique. Il compte une seule fois dans les histogrammes de neutrinos.
Les comptages utilisent les `event_group_ids` uniques, pas les lignes HDF5.
Les courbes de fraction CC comparent le Monte Carlo à sigma_CC/(sigma_CC+sigma_NC)
du modèle choisi ; les barres d'erreur sont des incertitudes binomiales de simulation.

## Contrôles

{len(checks)} contrôles réussis : nombres de primaires/showers, identités,
bornes de génération, inélasticités et relations E_had=y E_nu,
E_em=(1-y) E_nu. Détails dans `summary.json`.

## Figures

PNG pour les diapositives, SVG pour une version vectorielle. Style Matplotlib
simple, sans titres. Les axes indiquent si l'on compte des neutrinos ou des showers.

{figures_md}

## Exemple radio séparé

La figure radio, si présente, utilise une shower hadronique de 1 EeV à 1 km,
dans une glace homogène d'indice 1.78, avec Alvarez2009. Les trois angles sont
l'angle de Cherenkov, puis +1 et +2 degrés. Le spectre est normalisé au maximum
du spectre à l'angle de Cherenkov, commun aux trois courbes. Il n'inclut ni
atténuation de la glace, ni firn, ni antenne, ni bruit, ni trigger. Il illustre
le module d'émission ; ce n'est pas une simulation complète du détecteur.

## Suite scientifique

Valider une station et son trigger, choisir les modèles de production avec la
collaboration, ajouter l'absorption terrestre et les secondaires, puis simuler
les 35 stations et calculer A_eff(E, theta, phi) avec les incertitudes associées.
"""
    (args.output / "summary.md").write_text(report)
    print(f"\nPrimaries: {n:,}; CC: {ncc:,}; NC: {n-ncc:,}; showers: {len(data['energies']):,}")
    print(f"Checks passed: {len(checks)} / {len(checks)}")
    print(f"Report: {args.output / 'summary.md'}")
    print(f"Elapsed: {elapsed:.1f} s")


def main():
    started = time.perf_counter()
    args = arguments()
    args.output.mkdir(parents=True, exist_ok=True)
    path = get_input(args)
    data, primary, attrs = read_input(path)
    checks = validate(data, primary, attrs)
    model = attrs.get("preliminary_cross_sections_model", None)
    figures, radio_info = make_figures(data, primary, attrs, model, args.output,
                                      not args.skip_radio_example)
    write_summary(data, primary, attrs, path, args, checks, figures, radio_info,
                  time.perf_counter() - started)


if __name__ == "__main__":
    main()
