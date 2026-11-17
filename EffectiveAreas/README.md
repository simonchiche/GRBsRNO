# RNO-G directional effective-area project

Investigation date: 15 November 2026. Target agreed in the conversation:
instantaneous neutrino effective area `Aeff(E_nu, zenith, azimuth)` for GRBs
and other transients, ultimately for the planned 35-station array.

This is a working guide for implementing the calculation yourself. No detector
simulation or production event generation has been run for this investigation.
`GetEffectiveArea.py` was empty and has been left unchanged.

## Relevant material in the RNO-G GitHub organization

The supplied link, `https://github.com/RNO-G/`, is the organization rather than
one repository. Public repositories were inspected; access to private
collaboration repositories or the hardware database has not been established.

The most directly useful discovery is
[`RNO-G/analysis-tools/multimessenger_tools`](https://github.com/RNO-G/analysis-tools/tree/b7b68fec2a2ccdec2db4a9ad5e8e7af4d3d9fd64/multimessenger_tools).
Its `sensitivity.py` already reads effective volumes, converts them to areas,
transforms source positions, and averages response over an observation window.
There are example scripts and a dedicated `grb221009.py` analysis.

The bundled `data/Veff_fine_20.json` was inspected: 600 entries form 30 energy
bins from 10^15 to 10^20 eV and 20 equal-cos(zenith) bins. It contains threshold
proxy results from `1.50sigma` to `2.50sigma`, including `2.00sigma`. There are
no phi edges. This is a useful existing reference for the downstream GRB
calculation, but the JSON alone does not establish station count, geometry,
species mixture, cross-section model, or production revision. Verify that
provenance before adopting its normalization for a future array.

Specific points to review before reusing `sensitivity.py`:

- Its interpolator is a function of energy and zenith, without azimuth.
- It selects the `2.00sigma` proxy and uses the installed interaction-length
  default; set the intended trigger and cross-section convention explicitly.
- Its callable-FOV code explicitly flags an azimuth-convention mismatch.
- The default Summit coordinates are approximate and have a TODO in the source.
- `example.py` labels GRB221009A but uses a date in 2020. Supply the actual
  source coordinates and UTC event timestamp for each analysis.

These are reasons to use it as a reference and audit the assumptions while
building the new response table. The new generation/simulation work remains
necessary to predict a different detector configuration.

The organization also has a
[`RNO-G/NuRadioMC` fork](https://github.com/RNO-G/NuRadioMC).
The inspected default branch was `radiopropa-fix`, commit
[`f62e58631f964f59a78ecd0e42024341e9b9e81b`](https://github.com/RNO-G/NuRadioMC/tree/f62e58631f964f59a78ecd0e42024341e9b9e81b),
with package metadata `3.1.0-dev`. Its status as a validated production baseline
needs confirmation before selecting it for this project.
`rnog-env-builder` primarily builds the mattak/data-reader stack; that is useful
context but does not define this neutrino effective-area simulation.

## What the calculation consists of

```text
Neutrino interactions and shower properties (input HDF5)
  + detector geometry and responses
  + ice / emission / Earth-weight configuration
  + detector and trigger steering script
       |
       v
Askaryan emission -> propagation -> antenna/electronics -> noise and trigger
       |
       v
Simulation output HDF5 (+ optional .nur waveforms)
       |
       v
Weighted, unique triggered neutrinos -> Veff -> Aeff(E_nu, theta, phi)
       |
       v
GRB position and time -> local direction -> expected neutrino count
```

The first step generates interactions, including vertices, neutrino energies,
directions, flavours, interaction types, inelasticities, and shower properties.
It does not require simulating particle cascades with Geant4 or precomputing a
library of radio waveforms. The radio-emission model is evaluated during the
simulation. See the [effective-volume tutorial](https://nu-radio.github.io/NuRadioMC/NuRadioMC/pages/Manuals/veff_tutorial.html).

## Environment actually inspected

The default terminal `python3` is Python 3.9.1 at
`/Library/Frameworks/Python.framework/Versions/3.9/bin/python3`.
It imports NuRadioMC `2.3.0.dev0` from
`/Users/chiche/Library/Python/3.9/lib/python/site-packages/NuRadioMC`.
NuRadioReco is installed alongside it. The event generator, simulation class,
effective-volume utilities, and cross-section utilities import successfully.

The package installation metadata refers to an old source directory,
`/Users/chiche/Desktop/NuRadioMC`, which no longer exists. This does not prevent
imports from site-packages, but it means that path is not a usable checkout.
No compiled `.so` ray-tracing library was found beneath this installation's
`NuRadioMC/SignalProp`; simulation speed and ray-tracer availability still need
a separate check. Core imports alone do not establish simulation readiness.

The latest GitHub release returned by the release API was
[v3.1.0](https://github.com/nu-radio/NuRadioMC/releases/tag/v3.1.0).
The documentation and inspected development branch identify themselves as
3.2.0-dev. Development source was inspected at commit
[`0c42e0a817eb16e13b70c894a92a8abe1e09dc92`](https://github.com/nu-radio/NuRadioMC/tree/0c42e0a817eb16e13b70c894a92a8abe1e09dc92).

Use a dedicated environment and a recorded release or collaboration production
commit before producing physics results. The old installation can support the
first learning exercise. Do not combine example files from several versions
without checking their interfaces. See the [installation instructions](https://nu-radio.github.io/NuRadioMC/Introduction/pages/installation.html).

One concrete difference: the v3.1.0 generator accepts `cross_sections_model`;
the installed 2.3.0.dev0 generator does not. Another: the development RNO-G trigger
example has `--seed` and a beamformed power trigger; the v3.1.0 copy inspected
does not provide those same features. Commands must match the chosen version.

## Which scripts matter

Paths in the table are relative to the NuRadioMC repository root. In the current
installation, both `NuRadioMC` and `NuRadioReco` are beneath site-packages.

| File or directory | Role in this project |
| --- | --- |
| `NuRadioMC/EvtGen/generator.py` | Generate neutrino interactions with `generate_eventlist_cylinder`. |
| `NuRadioMC/examples/01_Veff_simulation/T01generate_event_list.py` | Small example of the generator API; its default volume is a South Pole example. |
| `NuRadioMC/examples/01_Veff_simulation/T02RunSimulation.py` | Shows how a steering class supplies filtering and trigger methods. Its example detector is not RNO-G. |
| `NuRadioMC/examples/07_RNO_G_simulation/RunSimulation.py` | Simple RNO-G steering example, available in the installed package. |
| `NuRadioMC/examples/07_RNO_G_simulation/RNO_config.yaml` | Example Greenland propagation and emission configuration. |
| `NuRadioMC/examples/RNO_G_trigger_simulation/simulate.py` | Newer RNO-G hardware/trigger simulation; absent from the installed 2.3.0.dev0 examples. |
| `NuRadioReco/detector/RNO_G/RNO_single_station.json` | Public idealized station geometry. |
| `NuRadioReco/detector/RNO_G/RNO_array.json` | Public planned array geometry, with 35 station entries and a 24-channel template. |
| `NuRadioMC/utilities/Veff.py` | Trigger combinations, duplicate removal, and effective-volume calculation. |
| `NuRadioMC/utilities/cross_sections.py` | Neutrino cross sections and interaction length. |
| `NuRadioMC/examples/06_webinar/W04EffectiveVolumes.py` | Useful worked postprocessing example; some explanatory comments are outdated. |
| `NuRadioMC/utilities/merge_hdf5.py` | Merge compatible simulation chunks while preserving total generated-event normalization. |
| `NuRadioMC/examples/03_station_coincidences/` | Additional examples for array geometry, jobs, and station coincidences. |

Source entry points: [basic workflow](https://github.com/nu-radio/NuRadioMC/tree/0c42e0a817eb16e13b70c894a92a8abe1e09dc92/NuRadioMC/examples/01_Veff_simulation),
[simple RNO-G example](https://github.com/nu-radio/NuRadioMC/tree/0c42e0a817eb16e13b70c894a92a8abe1e09dc92/NuRadioMC/examples/07_RNO_G_simulation),
[newer trigger example](https://github.com/nu-radio/NuRadioMC/blob/0c42e0a817eb16e13b70c894a92a8abe1e09dc92/NuRadioMC/examples/RNO_G_trigger_simulation/simulate.py),
[detector files](https://github.com/nu-radio/NuRadioMC/tree/0c42e0a817eb16e13b70c894a92a8abe1e09dc92/NuRadioReco/detector/RNO_G).

## What the RNO-G examples do and do not establish

The simple `07_RNO_G_simulation` example applies the hardware response and then
a high/low threshold of +/-20 mV on channel 0 alone, with one required channel.
Its YAML disables noise, selects `greenland_simple`, `GL1`, and `ARZ2020`.
This is an introductory configuration, not an established full-array forecast.

The newer trigger example handles the RNO-G signal chain, FLOWER digitization,
and a deep high/low coincidence trigger. The inspected development revision
also includes a beamformed power trigger. It adds noise through its own detector
simulation function; blindly enabling another noise path could add noise twice.
It selects a station and uses a hard-coded detector date of 3 February 2024,
which must be reviewed for a future detector model.

That example uses `rnog_detector.Detector`, querying the hardware database when
no exported detector description is supplied. A database export contains signal
chain information beyond the simple public geometry JSON. Do not assume that
`RNO_array.json` can be passed directly to that interface. See the
[RNO-G database documentation](https://nu-radio.github.io/NuRadioMC/NuRadioReco/pages/detector/rnog.html).

The older `NuRadioReco/examples/PhasedArray/Effective_volume/T02RunPhasedRNO.py`
illustrates beamforming, but describes a proposed configuration. Its filename
does not establish that it represents the final RNO-G trigger.

The installed `RNO_array.json` was instantiated successfully through
`GenericDetector` using the legacy station/channel fallback arguments. It
provided 35 stations with 24 channels each. Those arguments emit deprecation
warnings; explicit `reference_station` and `reference_channel` fields are the
preferred approach when preparing a new detector file.

Measured from the shipped file: nearest horizontal station separation is about
1229 m, and station coordinates span approximately x=[-1401, 7096] m and
y=[950, 8429] m. Therefore, a small cylinder centred at (0,0) does not cover this
array. Treat this as a historical public geometry to verify against the desired
future layout, not a current surveyed hardware description.

The [design paper, corrected v5](https://arxiv.org/html/2010.12279v5), especially
sections 6.3 and 6.4, provides directional benchmarks. Its Figure 26 uses a
35-station simulation with 1 km spacing and a simplified trigger, so agreement
requires matching those assumptions. The [2026 beamformed-trigger paper](https://arxiv.org/abs/2607.24470)
is a more recent reference for trigger modelling and validation.

## Effective volume, area, and solid angle

For a fixed energy and one neutrino species, with interactions thrown uniformly
in a known volume and a finite angular bin, the basic estimator is

```text
Veff_bin = V_generation / N_generated_bin * sum_unique_triggered(P_survival)
Aeff_bin = Veff_bin / L_interaction(E_nu)
```

Here `Aeff_bin` is an average over that angular bin, with area units. This is the
forced-interaction estimator; use the generation volume and normalization stored
in the file, including any full-volume extensions introduced for secondaries.
For the usual CC+NC sample, use the total interaction cross section. Samples
restricted to a process need the matching process normalization.

`cross_sections.get_interaction_length` supplies the interaction length. Keep its
cross-section model and density consistent with event generation and Earth
survival weights. In the inspected development code, the simulation default
YAML selects `ctw`, whereas the cross-section utility defaults to `hedis_bgr18`.
Set the model explicitly instead of relying on those defaults.

Keep species separate initially. Neutrino and antineutrino cross sections can
differ; dividing a mixed-species Veff by one arbitrarily chosen interaction
length is not the general conversion. Combine species areas using the fractions
of the flux convention you intend to use. A flux summed over all six species
uses a fraction-weighted area; a per-species flux is summed against its own area.

The Veff utilities return a volume without multiplying by solid angle and
without conversion to water equivalent. See the
[Veff API](https://nu-radio.github.io/NuRadioMC/NuRadioMC/apidoc/NuRadioMC.utilities.Veff.html)
and [interaction-length API](https://nu-radio.github.io/NuRadioMC/NuRadioMC/apidoc/NuRadioMC.utilities.cross_sections.html).
Raw ice Veff goes with the ice interaction length; water-equivalent Veff goes
with the water interaction length.

For angular bins in radians:

```text
DeltaOmega = (phi_max - phi_min) * (cos(theta_min) - cos(theta_max))
Acceptance(E) = sum_bins Aeff_bin(E) * DeltaOmega_bin       [area sr]
```

For a point source, use its directional area without multiplying by 4*pi or by
the bin solid angle. The angle-integrated acceptance is a different quantity.
For a flux differential in energy, the transient expectation is

```text
N_expected = sum_species integral dt integral dE
             flux_species(E,t) * Aeff_species(E, theta(t), phi(t))
```

Use a fluence directly for a sufficiently short burst with an effectively fixed
direction. Apply time-dependent station availability when predicting an actual
observation. Keep analysis-selection efficiency distinct from trigger efficiency.

## Specific issues for theta and phi tables

Generate isotropically within each chosen bin: uniform in cos(theta), uniform
in phi. The built-in cylinder generator implements this angular sampling.
Use finite bin widths rather than identical angular bounds.

The inspected `get_Veff_Aeff_array` helper indexes energy, zenith, trigger, and
five result statistics. There is no phi axis. Its intermediate dictionaries also
do not preserve phi edges as table coordinates. Mixing several phi bins at the
same energy and zenith can overwrite entries. Build a wrapper that retains phi
edges from each simulation file, or process each phi bin separately and assemble
the final table explicitly.

`oversampling_theta` offers finer zenith bins for an isotropic sample, with
normalization adjusted for the angular fraction. There is no corresponding phi
option in the inspected interface. If rebinning independently, the denominator
must account for the fraction of generated directions in each bin, not just
the number of triggered rows saved in the output.

NuRadio directions point toward the arrival direction: theta=0 comes from above,
theta=90 degrees is horizontal, and theta=180 degrees comes through the Earth.
Its local axes are x=east, y=north, z=up; phi runs northward from east.
Astronomical azimuth generally starts at north and runs toward east. Thus, for
that astronomical convention, `phi = (90 degrees - azimuth) mod 360 degrees`,
and `theta = 90 degrees - altitude`. Check that detector-grid orientations have
been mapped to these same axes. See the [coordinate conventions](https://nu-radio.github.io/NuRadioMC/Introduction/pages/conventions.html).

## Full-array counting and statistical checks

Count a neutrino once if any required trigger fires at any station. A neutrino
can produce several shower rows and trigger several stations. The relevant
identity is `event_group_ids`, not the row number. The Veff utility contains
duplicate removal for this reason.

`35 * Aeff_single_station` is a useful comparison, but a full-array prediction
needs the union of station detections in a shared spatial population. Adding
station areas counts coincidences repeatedly. Independently generated station
samples cannot simply be deduplicated by matching their numeric IDs.

For compatible independent chunks of the same energy/species/angular/geometry
configuration, merge outputs with the supplied merger before using the array
helper. Preserve zero-trigger chunks in the generated-event denominator. Do not
merge distinct phi bins as though they were repeated throws of the same bin.

Validation should include increasing the generation volume, loosening speedup
cuts, checking trigger combinations, and checking the coincidence fraction.
Retain the seeds, total generated primaries, volume, bin edges, configuration,
detector description, and code revision with every result.

For weighted events, monitor `N_eff = (sum w)^2 / sum(w^2)` after grouping by
primary neutrino. As a rough large-sample estimate, fractional Monte Carlo error
scales as `1/sqrt(N_eff)`. The supplied utility uses an approximate count-based
uncertainty; review uncertainty treatment before quoting precision in strongly
weighted bins. No triggers in a small sample does not establish zero acceptance.

## The implementation sequence

Before comparing physics outputs, establish the assumptions behind the existing
multimessenger response table. It gives a valuable independent check for the
postprocessing and sky-coordinate work while the new simulation is developed.

1. Choose a dedicated environment and record its code version. Prefer the
   collaboration's validated production revision when one is available.
2. Generate a small, primary-only nu_e sample at one energy and one angular bin.
   Inspect it before running any detector simulation.
3. Simulate one station and inspect a few triggered waveforms, weights, and IDs.
   First reproduce the introductory workflow, then validate the desired trigger.
4. Calculate one Veff and one Aeff; verify dimensions and normalization by hand.
5. Expand to energy and zenith bins, then phi bins. Keep species separate. A
   provisional production range is 10^16 to 10^20 eV, to refine after the pilot.
   Start with a coarse grid and allocate events based on observed precision.
6. Enable muon/tau secondaries with PROPOSAL and a Greenland configuration.
   Recheck volume extensions and event grouping; re-generate the input sample.
7. Validate the shared-volume full-array OR using the chosen 35-station geometry.
   Compare to the single-station scaling estimate and quantify coincidences.
8. Produce a table with energy, theta and phi edges, species, trigger, area,
   uncertainty, generated count, and effective count, plus provenance.
9. Convert each GRB sky position and UTC time to local coordinates and fold its
   spectrum/time profile with the table. Integrate source motion for long windows.

## First exercise to write and run yourself

This matches the installed 2.3.0.dev0 generator API. Save it as
`EffectiveAreas/01_generate_events.py` when ready. It generates one test bin,
not the production sky grid. The 5 km radius and 2.7 km depth are provisional
learning choices and require a volume-convergence study later.

```python
from NuRadioMC.EvtGen.generator import generate_eventlist_cylinder
from NuRadioReco.utilities import units

volume = {
    "fiducial_rmin": 0 * units.km,
    "fiducial_rmax": 5 * units.km,
    "fiducial_zmin": -2.7 * units.km,
    "fiducial_zmax": 0 * units.km,
}

generate_eventlist_cylinder(
    "pilot_nue_E18_theta55_65_phi0_30.hdf5",
    n_events=1000,
    Emin=1e18 * units.eV,
    Emax=1e18 * units.eV,
    volume=volume,
    thetamin=55 * units.deg,
    thetamax=65 * units.deg,
    phimin=0 * units.deg,
    phimax=30 * units.deg,
    flavor=[12],
    interaction_type="ccnc",
    deposited=False,
    proposal=False,
    seed=12345,
)
```

Run from `EffectiveAreas` using the interpreter we inspected:

```bash
python3 01_generate_events.py
```

`Emin == Emax` intentionally selects monoenergetic neutrinos; `deposited=False`
means the energy is the primary neutrino energy. `flavor=[12]` selects nu_e,
without anti-nu_e, to make the first interaction-length conversion unambiguous.
`proposal=False` omits secondary-lepton propagation in this learning sample.

Inspect the HDF5 with this separate snippet:

```python
import h5py
import numpy as np
from NuRadioReco.utilities import units

with h5py.File("pilot_nue_E18_theta55_65_phi0_30.hdf5", "r") as f:
    print("Generated primaries:", f.attrs["n_events"])
    print("Unique primary IDs:", len(np.unique(f["event_group_ids"][:])))
    print("Shower rows:", len(f["event_group_ids"]))
    print("Dataset names:", list(f.keys()))
    print("Volume [km^3]:", f.attrs["volume"] / units.km**3)
    print("Energy [eV]:", np.unique(f["energies"][:]) / units.eV)
    print("Flavours:", np.unique(f["flavors"][:]))
    print("Zenith range [deg]:", np.rad2deg([
        f["zeniths"][:].min(), f["zeniths"][:].max()
    ]))
    print("Azimuth range [deg]:", np.rad2deg([
        f["azimuths"][:].min(), f["azimuths"][:].max()
    ]))
```

Expect 1000 generated primaries, flavour 12, energy 10^18 eV, and angles inside
the requested bounds. Shower rows may exceed primary count because one neutrino
can generate both hadronic and electromagnetic showers. Do not interpret this
file as a triggered detector sample; it is the input to that next step.

The next discussion can use this input inspection and the available
collaboration detector/trigger setup to choose the first simulation steering
script together.
