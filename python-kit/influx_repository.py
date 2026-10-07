from dataclasses import dataclass
from influxdb_client_3 import InfluxDBClient3

@dataclass
class Detection:
    LegalName: str
    GeneratedIn: str
    UUID: str
    Latitude: float
    Longitude: float
    LocationUncertainty: int
    SourceType: str
    TrackID: int
    Category: str


class InfluxRepository:

    def __init__(self, host, token, database):

        self.client = InfluxDBClient3(
            host=host,
            token=token,
            database=database
        )

    def get_detections(self, hours=1):

        query = f"""
        SELECT *
        FROM "RinaSensors"
        """

        print("QUERY:")
        print(query)

        df = self.client.query(query=query, language="sql")

        print(f"Record trovati: {len(df)}")

        detections = []

        for _, row in df.iterrows():

            detection = Detection(
                LegalName=row.get("LegalName"),
                GeneratedIn=row.get("GeneratedIn"),
                UUID=row.get("UUID"),
                Latitude=float(row.get("Latitude", 0)),
                Longitude=float(row.get("Longitude", 0)),
                LocationUncertainty=int(row.get("LocationUncertainty", 0)),
                SourceType=row.get("SourceType"),
                TrackID=int(row.get("TrackID", 0)),
                Category=row.get("Category")
            )

            detections.append(detection)

        return detections

    def close(self):
        self.client.close()