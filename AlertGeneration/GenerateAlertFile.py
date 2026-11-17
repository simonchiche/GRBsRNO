import json
from datetime import datetime, timezone


def create_rnog_notice(
    energy_tev,
    neutrino_type,
    ra_deg,
    dec_deg,
    position_error_deg,
    event_id,
    event_time=None
):
    if event_time is None:
        event_time = datetime.now(timezone.utc)

    notice_time = datetime.now(timezone.utc)

    notice = {
        "title": "RNO-G NOTICE",
        "notice_type": "RNO-G Neutrino Candidate",

        "event_id": event_id,
        "event_type": neutrino_type,

        "event_time": event_time.isoformat(),

        "reconstructed_position": {
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "frame": "ICRS"
        },

        "position_error": {
            "radius_deg": position_error_deg,
            "probability": 0.90
        },

        "energy": {
            "value": energy_tev,
            "unit": "TeV"
        },

        "notice_time": notice_time.isoformat()
    }

    return notice


def save_notice(notice, filename):
    with open(filename, "w") as f:
        json.dump(notice, f, indent=4)


if __name__ == "__main__":

    notice = create_rnog_notice(
        energy_tev=1.0e5,
        neutrino_type="nu_mu CC",
        ra_deg=235.587,
        dec_deg=0.969,
        position_error_deg=1.2,
        event_id=123456,
        event_time=datetime(
            2026, 10, 1, 7, 32, 15,
            tzinfo=timezone.utc
        )
    )

    print(json.dumps(notice, indent=4))

    save_notice(
        notice,
        "rnog_notice_123456.json"
    )