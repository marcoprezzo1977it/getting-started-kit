from datetime import datetime
from io import BytesIO
from uuid import UUID, uuid4

import requests  # type: ignore

from models import (
    Anomaly,
    GeneratedBy,
    Geometry,
    Identifier,
    Intention,
    InvolvedObjectRel,
    Location,
    LocationRel,
    VigimareAlert,
    VigimareIndication,
    VigimareObject,
    VigimareVessel,
)
from models.common import XMLSerializable


def create_identifier(
    legalname: str | None = None,
    generated_in: datetime | str | None = None,
    uuid: UUID | None = None,
) -> Identifier | None:
    """
    Create an Identifier object with the given parameters.

    Args:
        legalname: Legal name for the generated_by field. Returns None if not provided.
        generated_in: Timestamp for generation. Defaults to current time if not provided.
        uuid: Unique identifier. Auto-generated if not provided.

    Returns:
        Identifier object or None if legalname is not provided.
    """
    if legalname is None:
        return None

    generated_by = GeneratedBy(legalname)

    if generated_in is None:
        generated_in = datetime.now().replace(microsecond=0).isoformat()

    if uuid is None:
        uuid = uuid4()

    return Identifier(generated_by, str(generated_in), uuid)


def create_location_rel(
    latitude: float | str | None = None,
    longitude: float | str | None = None,
    cog: float | None = None,
    heading: float | None = None,
    speed: float | None = None,
) -> LocationRel | None:
    """
    Create a LocationRel object from  coordinates and dynamic parameters.

    Args:
        latitude (float | str | None, optional): The latitude coordinate. Defaults to None.
        longitude (float | str | None, optional): The longitude coordinate. Defaults to None.
        cog (float | None, optional): Course over ground in degrees. Defaults to None.
        heading (float | None, optional): The heading direction in degrees. Defaults to None.
        speed (float | None, optional): The speed value. Defaults to None.

    Returns:
        LocationRel | None: A LocationRel object containing the location and navigation data,
            or None if both latitude and longitude are None.
    """
    if latitude is None and longitude is None:
        location_rel = None
    else:
        geometry = Geometry(latitude, longitude)
        location = Location(geometry)
        location_rel = LocationRel([location], cog, heading, speed)
    return location_rel


def create_involved_object_rel(
    involved_object: XMLSerializable | None,
) -> InvolvedObjectRel | None:
    if involved_object is not None:
        if isinstance(involved_object, VigimareVessel):
            involved_object.xsi_type = "vessel:VigimareVessel"
        elif isinstance(involved_object, VigimareObject):
            involved_object.xsi_type = "object:VigimareObject"
        else:
            raise ValueError("Involved object can only be of type VigimareVessel or VigimareObject")
        involved_object_rel = InvolvedObjectRel(Object=involved_object)
    else:
        involved_object_rel = None
    return involved_object_rel


def create_vigimare_object(
    legalname: str | None = None,
    generated_in: datetime | str | None = None,  # If none, will use NOW
    uuid: UUID | None = None,  # Will create new is None
    latitude: float | str | None = None,
    longitude: float | str | None = None,
    location_uncertainty: float | None = None,
    source_type: str | None = None,
    track_id: int | None = None,
    category: str | None = None,
) -> VigimareObject:
    """
    Create a VigimareObject with the specified parameters.

    Args:
        legalname (str | None, optional): Legal name for the identifier. Defaults to None.
        generated_in (datetime | str | None, optional): Timestamp for when the object was generated.
            If None, will use the current time (NOW). Defaults to None.
        uuid (UUID | None, optional): Unique identifier for the object. If None, a new UUID will be created.
            Defaults to None.
        latitude (float | str | None, optional): Latitude coordinate for the object's location. Defaults to None.
        longitude (float | str | None, optional): Longitude coordinate for the object's location. Defaults to None.
        location_uncertainty (float | None, optional): Uncertainty value for the location in meters. Defaults to None.
        source_type (str | None, optional): Type of source that generated this object. Defaults to None.
        track_id (int | None, optional): Tracking identifier for the object. Defaults to None.
        category (str | None, optional): Category classification for the object. Defaults to None.

    Returns:
        VigimareObject: A configured VigimareObject instance with the specified parameters.
    """

    identifier = create_identifier(legalname, generated_in, uuid)
    location_rel = create_location_rel(longitude, latitude)

    data_object = VigimareObject(
        Identifier=identifier,
        LocationRel=location_rel,
        LocationUncertainty=location_uncertainty,
        SourceType=source_type,
        TrackID=track_id,
        Category=category,
    )

    return data_object


def create_vigimare_vessel(
    legalname: str,
    generated_in: datetime | str | None = None,  # If none, will use NOW
    uuid: UUID | None = None,  # Will create new is None
    latitude: float | str | None = None,
    longitude: float | str | None = None,
    name: str | None = None,
    cog: float | None = None,
    heading: float | None = None,
    speed: float | None = None,
    breadth: float | None = None,
    call_sign: str | None = None,
    depth: float | None = None,
    draught: float | None = None,
    length: float | None = None,
    mmsi: int | None = None,
    navigational_status: str | None = None,
    ais_ship_type: int | None = None,
    source_type: str | None = None,
    track_id: int | None = None,
):
    """
    Create a VigimareVessel.

    Args:
        legalname: Legal name for the identifier
        generated_in: Generation timestamp (defaults to NOW if None)
        uuid: Unique identifier (creates new if None)
        latitude: Vessel latitude position
        longitude: Vessel longitude position
        name: Vessel name
        cog: Course over ground
        heading: Vessel heading
        speed: Vessel speed
        breadth: Vessel breadth
        call_sign: Vessel call sign
        depth: Vessel depth
        draught: Vessel draught
        length: Vessel length
        mmsi: Maritime Mobile Service Identity
        navigational_status: Current navigational status
        ais_ship_type: AIS ship type code
        source_type: Data source type
        track_id: Tracking identifier

    Returns:
        VigimareVessel data object
    """
    identifier = create_identifier(legalname, generated_in, uuid)
    location_rel = create_location_rel(longitude, latitude, cog, heading, speed)

    data_object = VigimareVessel(
        Identifier=identifier,
        Name=name,
        LocationRel=location_rel,
        Breadth=breadth,
        CallSign=call_sign,
        Depth=depth,
        Draught=draught,
        Length=length,
        MMSI=mmsi,
        NavigationalStatus=navigational_status,
        AisShipType=ais_ship_type,
        SourceType=source_type,
        TrackID=track_id,
    )
    return data_object


def create_vigimare_anomaly(anomaly_type: str, anomaly_score: float, explanation: str):
    data_object = Anomaly(anomaly_type, anomaly_score, explanation)

    return data_object


def create_vigimare_alert(
    legalname: str | None = None,
    generated_in: datetime | str | None = None,
    uuid: UUID | None = None,
    latitude: float | str | None = None,
    longitude: float | str | None = None,
    involved_object: XMLSerializable | None = None,
    anomaly: Anomaly | None = None,
    intentions: list[Intention] | None = None,
):
    """
    Create a Vigimare alert object with the specified parameters.

    Args:
        legalname (str | None, optional): Legal name for the identifier. Defaults to None.
        generated_in (datetime | str | None, optional): Timestamp when the alert was generated.
            If None, will use current time (NOW). Defaults to None.
        uuid (UUID | None, optional): Unique identifier for the alert.
            Will create a new UUID if None. Defaults to None.
        latitude (float | str | None, optional): Latitude coordinate for the alert location.
            Defaults to None.
        longitude (float | str | None, optional): Longitude coordinate for the alert location.
            Defaults to None.
        involved_object (XMLSerializable | None, optional): Object involved in the alert.
            Defaults to None.
        anomaly (Anomaly | None, optional): Anomaly information associated with the alert.
            Defaults to None.
        intentions (list[Intention] | None, optional): List of intentions related to the alert.
            Defaults to None.

    Returns:
        VigimareAlert: A configured VigimareAlert data object with all specified parameters.

    Note:
        - The function automatically sets the namespace prefix to "vigimare" for anomaly and intentions.
        - Helper functions create_identifier, create_location_rel, and create_involved_object_rel
          are used to construct the respective components.
    """
    identifier = create_identifier(legalname, generated_in, uuid)
    location_rel = create_location_rel(longitude, latitude)
    involved_object_rel = create_involved_object_rel(involved_object)

    if anomaly is not None:
        anomaly.ns_prefix = "vigimare"
    if intentions is not None:
        for intention in intentions:
            intention.ns_prefix = "vigimare"

    data_object = VigimareAlert(
        Identifier=identifier,
        LocationRel=location_rel,
        InvolvedObjectRel=involved_object_rel,
        Intentions=intentions,
        Anomaly=anomaly,
    )

    return data_object


def create_vigimare_indication(
    legalname: str | None = None,
    generated_in: datetime | str | None = None,  # If none, will use NOW
    uuid: UUID | None = None,  # Will create new is None
    latitude: float | str | None = None,
    longitude: float | str | None = None,
    involved_object: XMLSerializable | None = None,
    indication_type: str = "",
    indication_value: str = "",
    explanation: str | None = None,
):
    """
    Create a Vigimare indication object with specified parameters.

    Args:
        legalname (str | None, optional): Legal name for the identifier. Defaults to None.
        generated_in (datetime | str | None, optional): Timestamp for when the indication was generated.
            If None, uses current timestamp. Defaults to None.
        uuid (UUID | None, optional): Unique identifier. If None, a new UUID will be created. Defaults to None.
        latitude (float | str | None, optional): Latitude coordinate for the location. Defaults to None.
        longitude (float | str | None, optional): Longitude coordinate for the location. Defaults to None.
        involved_object (XMLSerializable | None, optional): Object involved in the indication. Defaults to None.
        indication_type (str, optional): Type of the indication. Defaults to "".
        indication_value (str, optional): Value of the indication. Defaults to "".
        explanation (str | None, optional): Additional explanation for the indication. Defaults to None.
    """

    identifier = create_identifier(legalname, generated_in, uuid)
    location_rel = create_location_rel(longitude, latitude)
    involved_object_rel = create_involved_object_rel(involved_object)
    data_object = VigimareIndication(
        Identifier=identifier,
        LocationRel=location_rel,
        InvolvedObjectRel=involved_object_rel,
        IndicationType=indication_type,
        IndicationValue=indication_value,
        Explanation=explanation,
    )

    return data_object


def validate(xml_str: str):
    file_like = BytesIO(xml_str.encode("utf-8"))

    response = requests.post(
        "https://vigimare.ri.se/api/v1/validate-file",
        files={"file": ("file.xml", file_like, "application/xml")},
    )
    return response.json()
