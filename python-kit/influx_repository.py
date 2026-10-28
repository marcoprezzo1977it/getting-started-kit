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

    def get_detections(
        self,
        start_time="2026-10-05T09:01:45",
        end_time="2026-10-05T09:02:40"
    ):
        table_name = "RinaSensors"

        # Evita valori non numerici o negativi nell'INTERVAL SQL
        print(f"Range ricerca: {start_time} -> {end_time}")

        query = f"""
        WITH sound AS (
            SELECT
                time,
                "TrackID",
                "Category",
                "Acoustic",
                "Thermal",
                "Visible",
                "LocationUncertainty",
                "SensorName",
                "TagId"
            FROM "{table_name}"
            WHERE "SensorName" = 'SoundCam'
            AND "TagId" = 'Warnings'
            AND "TrackID" IS NOT NULL
            AND time >= '{start_time}'
            AND time <= '{end_time}'
        ),

        gps AS (
            SELECT
                time,
                "Latitude",
                "LatBaseLine",
                "Longitude",
                "LongBaseLine",
                "Validity"
            FROM "{table_name}"
            WHERE "SensorName" = 'RTK3BPro'
            AND "TagId" = '$GNRMC'
            AND time >= '{start_time}'
            AND time <= '{end_time}'
        ),

        heading AS (
            SELECT
                time,
                "Heading",
                "HeadingStdDev",
                "Pitch",
                "PitchStdDev"
            FROM "{table_name}"
            WHERE "SensorName" = 'RTK3BPro'
            AND "TagId" = '#UNIHEADINGA'
            AND time >= '{start_time}'
            AND time <= '{end_time}'
        )

        SELECT
            sound.time,
            sound."TrackID",
            sound."Category",
            sound."Acoustic",
            sound."Thermal",
            sound."Visible",
            sound."LocationUncertainty",

            gps."Latitude",
            gps."LatBaseLine",
            gps."Longitude",
            gps."LongBaseLine",
            gps."Validity",

            heading."Heading",
            heading."HeadingStdDev",
            heading."Pitch",
            heading."PitchStdDev"

        FROM sound

        LEFT JOIN gps
            ON sound.time = gps.time

        LEFT JOIN heading
            ON sound.time = heading.time

        ORDER BY
            sound."TrackID",
            sound.time
        """
#        print("QUERY:")
#        print(query)

        df = self.client.query(
            query=query,
            language="sql"
        ).to_pandas()

        print(f"Record trovati: {len(df)}")
 #       print("COLONNE:")
 #       print(df.columns.tolist())

        detections = []

        if df.empty:
            return detections

        # Mantiene soltanto le righe collegate a una posizione GPS
        df = df.dropna(subset=["Latitude", "Longitude"])

        track_ids = df["TrackID"].dropna().unique().tolist()
        print(f"TrackID trovati: {track_ids}")

        for track_id, track_df in df.groupby("TrackID", sort=False):

            print(f"Elaborazione TrackID: {track_id}")
            print(f"Righe associate: {len(track_df)}")

            for _, row in track_df.iterrows():

                print("RIGA ESTRATTA:")
                print(row.to_dict())

                # Calcolo dei nuovi campi a partire dalla riga completa
                newLat, newLon = calcola_centro_cerchio(row)

                detection = Detection(
                    LegalName=safe_string(table_name),

                    GeneratedIn=safe_string(
                        pd.to_datetime(row["time"], utc=True).isoformat()
                    ),

                    UUID=str(uuid.uuid4()),

                    # Posizione RTK/GPS originale
                    Latitude=safe_number(row.get("Latitude")),
                    Longitude=safe_number(row.get("Longitude")),

                    # Posizione calcolata
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

                    # Se Detection prevede questi attributi,
                    # puoi aggiungerli qui:
                    #
                    # Acoustic=safe_int(row.get("Acoustic")),
                    # Thermal=safe_int(row.get("Thermal")),
                    # Visible=safe_int(row.get("Visible")),
                    # Heading=safe_number(row.get("Heading")),
                    # HeadingStdDev=safe_number(row.get("HeadingStdDev")),
                    # Pitch=safe_number(row.get("Pitch")),
                    # PitchStdDev=safe_number(row.get("PitchStdDev")),
                    # Validity=safe_string(row.get("Validity")),
                )

                detections.append(detection)

        print(f"Detection generate: {len(detections)}")

        return detections


    def close(self):
        self.client.close()