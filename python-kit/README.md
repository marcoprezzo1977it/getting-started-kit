# Python-kit

This folder contains Python scripts that may prove helpful when creating Vigimare XML messages, validating them, as well as sending and receiving them via a Kafka server.

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for package management. Please [install UV](https://docs.astral.sh/uv/getting-started/installation/) first, then run

```bash
uv sync
```
to install the dependencies.

## Usage

Below follows some examples how to create XML messages. They are found in the `main.py` file. Test run this

```bash
uv run main.py
```

## Sending and receiving messages over Kafka

First, run the local kafka server. See instructions in [../local-kafka/README.md](../local-kafka/README.md).

Then run the script that starts to produce messages

```bash
uv run kafka_producer.py
```

and then, in another terminal, run

```bash
uv run kafka_consumer.py
```

to start listening on the topic and consuming messages.

Check the code inside these files to see how you can set up this for yourself.


## Validation

All created objects can be validated using the `validate()` function, which checks the XML against the Vigimare schema:

```python
linter_result = validate(vigimare_object.to_string())
```

This uses the linter API that is available at the URL `https://vigimare.ri.se/api/v1/validate-file`. It is also possible to visit [https://vigimare.ri.se](https://vigimare.ri.se) and copy paste the full message into the graphical user interface and validate the message.

## Examples

### Creating a Vigimare Object

```python
from utils.helper_functions import create_vigimare_object, validate

vigimare_object = create_vigimare_object(
    legalname="My object tracking service",
    generated_in=None,  # Will automatically create timestamp using the current time
    uuid=None,  # Will automatically create UUID
    latitude=24.1251,
    longitude=54.1251,
    location_uncertainty=20.0,
    source_type="Satellite",
    track_id=1234567,
    category="Drone",
)
xml_string = vigimare_object.to_string(indent=2)
linter_result = validate(xml_string)
print(linter_result)

>> {'status': 'Linting was successful '}
```

### Creating a Vigimare Vessel

```python
from datetime import datetime, timezone
from utils.helper_functions import create_vigimare_vessel, validate

vigimare_vessel = create_vigimare_vessel(
    legalname="My AIS service",
    generated_in=datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc).isoformat(),
    uuid=None,  # Will be generated
    latitude=59.3293,
    longitude=18.0686,
    name="Titanic",
    cog=90.0,
    heading=85.0,
    speed=12.5,
    breadth=5,
    call_sign="ABCD",
    depth=1.8,
    draught=1.8,
    length=15.0,
    mmsi=265513270,
    navigational_status="UnderWayUsingEngine",
    ais_ship_type=50,
    source_type="AIS"
)

xml_string = vigimare_vessel.to_string(indent=2)
linter_result = validate(xml_string)
print(linter_result)

>> {'status': 'Linting was successful '}
```

### Creating a Vigimare Alert containing an anomaly

```python
from utils.helper_functions import (
    create_vigimare_alert,
    create_vigimare_anomaly,
    create_vigimare_object,
    validate,
)

vigimare_anomaly = create_vigimare_anomaly(
    "Unexpected route", 0.81, "Here you provide an explanation"
)

# An object that is triggering the alert
vigimare_object = create_vigimare_object(
    legalname="My object tracking service",
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

linter_result = validate(vigimare_alert.to_string())
print(linter_result)

>> {'status': 'Linting was successful '}
```

### Creating a Vigimare Indication

This example creates an indication with an involved vigimare object with a specified track id. This could be from radar for example.

```python
from utils.helper_functions import (
    create_vigimare_indication,
    create_vigimare_object,
    validate,
)

# An object that is triggering the indication
vigimare_object = create_vigimare_object(
    legalname="My object tracking service",
    track_id=1234567,
)

vigimare_indication = create_vigimare_indication(
    legalname="My analysis service",
    latitude=24.1251,
    longitude=54.1251,
    involved_object=vigimare_object, # Insert it here
    indication_type="DarkVessel",
    indication_value="True",
    explanation="Dark vessel detected",
)

linter_result = validate(vigimare_indication.to_string())
print(linter_result)

>> {'status': 'Linting was successful '}
```
