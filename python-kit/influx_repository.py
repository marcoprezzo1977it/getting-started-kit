import pandas as pd
import uuid
from dataclasses import dataclass
from influxdb_client_3 import InfluxDBClient3
import math
  
def conversione_NMEA(value, baseline):

    if value is None or pd.isna(value):
        return None

    value = float(value)

    degrees = int(value / 100)
    minutes = value - (degrees * 100)

    decimal = degrees + (minutes / 60)

    if baseline in ("S", "W"):
        decimal = -decimal

    return decimal

def calcola_centro_cerchio(row):

    R = 6371000  # raggio terrestre in metri
    D = 250      # distanza in metri

    print("\n========== CALCOLO CENTRO CERCHIO ==========")

    # Valori ORIGINALI da Influx
    print("--- INPUT INFLUX ---")
    print(f"Latitude originale     : {row.get('Latitude')}")
    print(f"LatBaseLine             : {row.get('LatBaseLine')}")
    print(f"Longitude originale    : {row.get('Longitude')}")
    print(f"LongBaseLine            : {row.get('LongBaseLine')}")
    print(f"Heading                 : {row.get('Heading')}")

    # Conversione NMEA -> gradi decimali
    lat_dec = conversione_NMEA(
        row.get("Latitude"),
        row.get("LatBaseLine")
    )

    lon_dec = conversione_NMEA(
        row.get("Longitude"),
        row.get("LongBaseLine")
    )

    print("\n--- CONVERSIONE NMEA ---")
    print(f"Latitude decimale       : {lat_dec}")
    print(f"Longitude decimale      : {lon_dec}")

    heading = row.get("Heading")

    if lat_dec is None:
        print("ERRORE: lat_dec è None")
        return None, None

    if lon_dec is None:
        print("ERRORE: lon_dec è None")
        return None, None

    if heading is None:
        print("ERRORE: Heading è None")
        return None, None

    if pd.isna(heading):
        print("ERRORE: Heading è NaN")
        return None, None

    # Conversione in radianti
    lat = math.radians(lat_dec)
    lon = math.radians(lon_dec)
    bearing = math.radians(float(heading))

    print("\n--- CONVERSIONE RADIANTI ---")
    print(f"lat radians             : {lat}")
    print(f"lon radians             : {lon}")
    print(f"bearing radians         : {bearing}")

    delta = D / R

    print(f"delta                    : {delta}")

    # Calcolo nuova latitudine
    newLat = math.asin(
        math.sin(lat) * math.cos(delta)
        + math.cos(lat) * math.sin(delta) * math.cos(bearing)
    )

    # Calcolo nuova longitudine
    newLon = lon + math.atan2(
        math.sin(bearing) * math.sin(delta) * math.cos(lat),
        math.cos(delta) - math.sin(lat) * math.sin(newLat)
    )

    print("\n--- RISULTATO IN RADIANTI ---")
    print(f"newLat radians          : {newLat}")
    print(f"newLon radians          : {newLon}")

    # Conversione radianti -> gradi
    newLat = math.degrees(newLat)
    newLon = math.degrees(newLon)

    print("\n--- RISULTATO IN GRADI PRIMA NORMALIZZAZIONE ---")
    print(f"newLat                  : {newLat}")
    print(f"newLon                  : {newLon}")

    # Normalizzazione longitudine [-180, +180]
    newLon = ((newLon + 540) % 360) - 180

    print("\n--- RISULTATO FINALE ---")
    print(f"newLat FINALE           : {newLat}")
    print(f"newLon FINALE           : {newLon}")
    print("=============================================\n")

    return newLat, newLon
 
def safe_number(value):
    return 0 if pd.isna(value) else value
 
def safe_string(value):
    return "-" if pd.isna(value) else str(value)

def safe_int(value, default=0):
    return int(value) if pd.notna(value) else default

def nmea_to_decimal(value, direction):
    value = float(value)

    degrees = int(value // 100)
    minutes = value - (degrees * 100)

    decimal = degrees + minutes / 60

    if direction in ("S", "W"):
        decimal = -decimal

    return decimal

def get_source_type(row):
    for field in ["Acoustic", "Thermal", "Visual"]:
        if field in row.index and not pd.isna(row[field]):
            return field
 
    return "-"

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
    newLat: float | None = None
    newLon: float | None = None


class InfluxRepository:

    def __init__(self, host, token, database):

        self.client = InfluxDBClient3(
            host=host,
            token=token,
            database=database
        )


    def get_detections(self, hours=1):

        table_name = "RinaSensors"

        query = f"""
        SELECT *
        FROM "{table_name}"
        """

        print("QUERY:")
        print(query)

        df = self.client.query(
            query=query,
            language="sql"
        ).to_pandas()

        print(f"Record trovati: {len(df)}")

        detections = []

        print("COLONNE:")
        print(df.columns.tolist())

        if df.empty:
            return detections

        print("PRIMO RECORD:")
        print(df.iloc[0].to_dict())

        df = df.dropna(subset=["Latitude", "Longitude"])

        for _, row in df.iterrows():

            print("RIGA ESTRATTA")
            print(row.to_dict())

            # Calcolo dei NUOVI campi
            newLat, newLon = calcola_centro_cerchio(row)

            detection = Detection(
                LegalName=safe_string(table_name),

                GeneratedIn=safe_string(
                    pd.to_datetime(row["time"], utc=True).isoformat()
                ),

                UUID=str(uuid.uuid4()),

                # Valori ORIGINALI provenienti da InfluxDB
                Latitude=safe_number(row["Latitude"]),
                Longitude=safe_number(row["Longitude"]),

                # Nuovi valori CALCOLATI
                newLat=safe_number(newLat),
                newLon=safe_number(newLon),

                LocationUncertainty=safe_number(
                    row.get("LocationUncertainty")
                ),

                SourceType=get_source_type(row),

                TrackID=safe_int(
                    row.get("TrackID")
                ),

                Category=safe_string(
                    row.get("Category")
                )
            )

            detections.append(detection)

        return detections

    def close(self):
        self.client.close()