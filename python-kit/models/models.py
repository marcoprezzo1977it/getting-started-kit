from dataclasses import dataclass

from .common import Identifier, LocationRel, XMLSerializable


@dataclass
class Anomaly(XMLSerializable):
    AnomalyType: str
    AnomalyScore: float
    Explanation: str


@dataclass
class Intention(XMLSerializable):
    Classification: str
    Probability: float
    Explanation: str


@dataclass
class VigimareObject(XMLSerializable):
    Identifier: Identifier | None
    LocationRel: LocationRel | None
    LocationUncertainty: float | None
    SourceType: str | None
    TrackID: int | None
    Category: str | None


@dataclass
class VigimareVessel(XMLSerializable):
    Identifier: Identifier | None
    Name: str | None
    LocationRel: LocationRel | None
    Breadth: float | None
    CallSign: str | None
    Depth: float | None
    Draught: float | None
    Length: float | None
    MMSI: int | None
    NavigationalStatus: str | None
    AisShipType: int | None
    SourceType: str | None
    TrackID: int | None


@dataclass
class InvolvedObjectRel(XMLSerializable):
    Object: VigimareVessel | VigimareObject


@dataclass
class VigimareAlert(XMLSerializable):
    Identifier: Identifier | None
    LocationRel: LocationRel | None
    InvolvedObjectRel: InvolvedObjectRel | None
    Intentions: list[Intention] | None
    Anomaly: Anomaly | None


@dataclass
class VigimareIndication(XMLSerializable):
    Identifier: Identifier | None
    LocationRel: LocationRel | None
    InvolvedObjectRel: InvolvedObjectRel | None
    IndicationType: str
    IndicationValue: str
    Explanation: str | None
