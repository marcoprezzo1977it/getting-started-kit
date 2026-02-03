from datetime import datetime, timezone

from utils.helper_functions import (
    create_vigimare_alert,
    create_vigimare_anomaly,
    create_vigimare_indication,
    create_vigimare_object,
    create_vigimare_vessel,
    validate,
)

if __name__ == "__main__":
    # Create a vigimare object
    vigimare_object = create_vigimare_object(
        legalname="My object tracking service",
        generated_in=None,  # Will automatically create timestamp using the current time
        uuid=None,  # Will automatically create UUID
        latitude=24.1251,
        longitude=54.1251,
        location_uncertainty=0.99,
        source_type="Satellite",
        track_id=1234567,
        category="Drone",
    )
    print(vigimare_object.to_string(indent=4) + "\n")
    linter_result = validate(vigimare_object.to_string())
    print(linter_result)

    # Create a vigimare vessel
    vigimare_vessel = create_vigimare_vessel(
        legalname="My AIS service",
        generated_in=datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc).isoformat(),
        uuid=None,  # Will be generated
        latitude=59.3293,
        longitude=18.0686,
        name="SGAJ",
        cog=90.0,
        heading=85.0,
        speed=12.5,
        breadth=5,
        call_sign="SGAJ",
        depth=1.8,
        draught=1.8,
        length=15.0,
        mmsi=265513270,
        navigational_status="UnderWayUsingEngine",
        ais_ship_type=50,
        source_type="AIS",
    )
    print("\n" + vigimare_vessel.to_string() + "\n")
    linter_result = validate(vigimare_vessel.to_string())
    print(linter_result)

    # Create a vigimare alert
    vigimare_anomaly = create_vigimare_anomaly("Unexpected route", 0.81, "Here you provide an explanation")
    vigimare_vessel = create_vigimare_object(
        legalname="My sensor service",
        track_id=1234567,
    )
    vigimare_alert = create_vigimare_alert(
        legalname="My analysis service",
        latitude=24.1251,
        longitude=54.1251,
        involved_object=vigimare_object,
        anomaly=vigimare_anomaly,
        intentions=None,
    )

    print("\n" + vigimare_alert.to_string() + "\n")
    linter_result = validate(vigimare_alert.to_string())
    print(linter_result)

    # Create a vigimare indication
    vigimare_indication = create_vigimare_indication(
        legalname="My analysis service",
        latitude=24.1251,
        longitude=54.1251,
        involved_object=vigimare_object,
        indication_type="DarkVessel",
        indication_value="True",
        explanation="Dark vessel detected",
    )
    print("\n" + vigimare_indication.to_string() + "\n")
    linter_result = validate(vigimare_indication.to_string())
    print(linter_result)
