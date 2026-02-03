import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, fields
from typing import cast
from uuid import UUID
from xml.etree.ElementTree import QName


@dataclass
class XMLMixin:
    namespaces: dict[str, str] = field(
        default_factory=lambda: {
            "vigimare": "https://github.com/vigimare/xsd",
            "object": "http://www.cise.eu/datamodel/v1/entity/object/",
            "vessel": "http://www.cise.eu/datamodel/v1/entity/vessel/",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
        init=False,
    )
    xsi_type: str | None = field(default=None, init=False)
    ns_prefix: str | None = field(default=None, init=False)


@dataclass
class XMLSerializable(XMLMixin):
    def serialize(self, ns_prefix=None):
        """
        Serialize the object to an XML Element.

        This method converts the current object instance into an XML Element representation,
        handling nested objects, lists, and attributes according to XML serialization rules.

        Args:
            ns_prefix (str, optional): The namespace prefix to use for the root element.
                If provided, the corresponding namespace URI will be retrieved from the
                object's namespaces dictionary. Defaults to None.

        Returns:
            xml.etree.ElementTree.Element: An XML Element representing the serialized object.
                The element includes:
                - Namespace-qualified tags (if ns_prefix is provided)
                - XSI type information (if xsi_type is set)
                - Child elements for all non-None, non-excluded fields
                - Proper handling of nested XMLSerializable objects and lists

        Raises:
            ValueError: If xsi_type is set but doesn't contain a colon separator in the
                format "namespace:ClassName".

        Notes:
            - Fields named "namespaces", "xsi_type", and "ns_prefix" are excluded from serialization
            - List items and nested XMLSerializable objects are recursively serialized
            - Namespaces are automatically registered with ElementTree
            - When xsi_type is set, the root tag becomes "Object" with an xsi:type attribute
        """
        ns_uri = self.namespaces.get(ns_prefix) if (self.namespaces and ns_prefix) else None

        tag = f"{{{ns_uri}}}{self.__class__.__name__}" if ns_uri else self.__class__.__name__

        tag = tag if not self.xsi_type else "Object"

        root = ET.Element(tag)

        if self.namespaces:
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)

        if self.xsi_type:
            if ":" not in self.xsi_type:
                raise ValueError("Make sure that the xsi_type is a string on the form namespace:SomeClass")

            xsi_uri = self.namespaces.get("xsi") if self.namespaces else None
            if xsi_uri:
                type_ns, class_name = self.xsi_type.split(":")
                type_ns_uri = self.namespaces.get(type_ns)

                root.set(f"{{{xsi_uri}}}type", QName(type_ns_uri, class_name))  # type: ignore

        for f in fields(self):
            value = getattr(self, f.name, None)
            if value is None or f.name in ("namespaces", "xsi_type", "ns_prefix"):
                continue

            if isinstance(value, list):
                for item in value:
                    # print(f"VALUE {item}" + "###" * 100)
                    if isinstance(item, XMLSerializable):
                        item = cast(XMLSerializable, item)
                        root.append(item.serialize(getattr(item, "ns_prefix", None)))
                    else:
                        child_tag = f"{{{ns_uri}}}{f.name}" if ns_uri else f.name
                        child = ET.SubElement(root, child_tag)
                        child.text = str(item)

            elif isinstance(value, XMLSerializable):
                root.append(value.serialize(getattr(value, "ns_prefix", None)))

            else:
                child_tag = f"{{{ns_uri}}}{f.name}" if ns_uri else f.name
                child = ET.SubElement(root, child_tag)
                child.text = str(value)

        return root

    def to_string(self, indent: int = 2):
        xml = self.serialize()
        ET.indent(xml, space=" " * indent)
        return ET.tostring(xml, encoding="unicode")


@dataclass
class GeneratedBy(XMLSerializable):
    LegalName: str | None


@dataclass
class Identifier(XMLSerializable):
    GeneratedBy: GeneratedBy
    GeneratedIn: str | None
    UUID: UUID | None


@dataclass
class Geometry(XMLSerializable):
    Latitude: float | str | None
    Longitude: float | str | None


@dataclass
class Location(XMLSerializable):
    Geometry: Geometry


@dataclass
class LocationRel(XMLSerializable):
    Location: list[Location]
    COG: float | None = None
    Heading: float | None = None
    Speed: float | None = None
