import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


VOEVENT_NS = "http://www.ivoa.net/xml/VOEvent/v2.0"


def to_utc_iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return (
        dt.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def create_rnog_notice(
    energy_tev,
    neutrino_type,
    ra_deg,
    dec_deg,
    position_error_deg,
    event_id,
    event_time=None,
    format="json"
):

    if event_time is None:
        event_time = datetime.now(timezone.utc)

    notice_time = datetime.now(timezone.utc)

    if format.lower() == "json":

        notice = {
            "title": "RNO-G NOTICE",
            "notice_type": "RNO-G Neutrino Candidate",

            "event_id": event_id,
            "event_type": neutrino_type,

            "event_time": to_utc_iso(event_time),

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

            "notice_time": to_utc_iso(notice_time)
        }

        return json.dumps(notice, indent=4)


    elif format.lower() == "voevent":

        ET.register_namespace("voe", VOEVENT_NS)

        root = ET.Element(
            f"{{{VOEVENT_NS}}}VOEvent",
            {
                "ivorn": f"ivo://rnog.org/alerts#{event_id}",
                "role": "test",
                "version": "2.0"
            }
        )

        # WHO
        who = ET.SubElement(root, "Who")

        date = ET.SubElement(who, "Date")
        date.text = to_utc_iso(notice_time)


        # WHAT
        what = ET.SubElement(root, "What")

        ET.SubElement(
            what,
            "Param",
            {
                "name": "event_id",
                "value": str(event_id),
                "dataType": "string"
            }
        )

        ET.SubElement(
            what,
            "Param",
            {
                "name": "neutrino_type",
                "value": neutrino_type,
                "dataType": "string"
            }
        )

        ET.SubElement(
            what,
            "Param",
            {
                "name": "energy",
                "value": str(energy_tev),
                "unit": "TeV",
                "dataType": "float"
            }
        )


        # WHERE + WHEN
        wherewhen = ET.SubElement(root, "WhereWhen")

        obs_data_location = ET.SubElement(
            wherewhen,
            "ObsDataLocation"
        )

        ET.SubElement(
            obs_data_location,
            "ObservatoryLocation",
            {"id": "RNO-G"}
        )

        observation_location = ET.SubElement(
            obs_data_location,
            "ObservationLocation"
        )

        ET.SubElement(
            observation_location,
            "AstroCoordSystem",
            {"id": "UTC-ICRS-TOPO"}
        )

        astro_coords = ET.SubElement(
            observation_location,
            "AstroCoords",
            {"coord_system_id": "UTC-ICRS-TOPO"}
        )


        # TIME
        time = ET.SubElement(
            astro_coords,
            "Time",
            {"unit": "s"}
        )

        time_instant = ET.SubElement(
            time,
            "TimeInstant"
        )

        iso_time = ET.SubElement(
            time_instant,
            "ISOTime"
        )

        iso_time.text = to_utc_iso(event_time)


        # POSITION
        position = ET.SubElement(
            astro_coords,
            "Position2D",
            {"unit": "deg"}
        )

        value2 = ET.SubElement(
            position,
            "Value2"
        )

        c1 = ET.SubElement(value2, "C1")
        c1.text = str(ra_deg)

        c2 = ET.SubElement(value2, "C2")
        c2.text = str(dec_deg)

        error = ET.SubElement(
            position,
            "Error2Radius"
        )

        error.text = str(position_error_deg)

        ET.indent(root, space="    ")

        return ET.tostring(
            root,
            encoding="unicode",
            xml_declaration=True
        )


    else:
        raise ValueError(
            "format must be 'json' or 'voevent'"
        )


def save_notice(notice, filename):
    with open(filename, "w") as f:
        f.write(notice)


if __name__ == "__main__":

    parameters = {
        "energy_tev": 1.0e5,
        "neutrino_type": "nu_mu CC",
        "ra_deg": 235.587,
        "dec_deg": 0.969,
        "position_error_deg": 1.2,
        "event_id": "RNO-G_20261001_001",
        "event_time": datetime(
            2026, 10, 1, 7, 32, 15,
            tzinfo=timezone.utc
        )
    }


    # JSON
    json_notice = create_rnog_notice(
        **parameters,
        format="json"
    )

    print(json_notice)

    save_notice(
        json_notice,
        "rnog_notice.json"
    )


    # VOEvent
    voevent_notice = create_rnog_notice(
        **parameters,
        format="voevent"
    )

    print(voevent_notice)

    save_notice(
        voevent_notice,
        "rnog_notice.xml"
    )