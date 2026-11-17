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