import signal
import time
import logging
import os

from datetime import datetime
from dotenv import load_dotenv
from kafka import KafkaProducer
from utils.helper_functions import create_vigimare_vessel
from utils.helper_functions import create_vigimare_object

from influx_repository import InfluxRepository
from dataclasses import dataclass
from configInflux import (
    INFLUX_URL,
    INFLUX_TOKEN,
    INFLUX_ORG,
    INFLUX_BUCKET
)

SERVICE_NAME = "My vigimare object test service"
#KAFKA_TOPIC = "rina-test123"
LOCATION_UNCERTAINLY = 250

MODE_STATE = "test"   # "test" oppure "prod"

TEST_START_TIME = datetime.fromisoformat(
    "2026-10-05T09:02:27+00:00"
)

STATE_FILE = "watermark.json"

import json
import os
from datetime import datetime, timezone, timedelta

STATE_FILE = "watermark.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return None, {}

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)

        watermark = data.get("watermark")

        if watermark:
            watermark = datetime.fromisoformat(watermark)

        tracks = data.get("tracks", {})

        # JSON salva le chiavi come stringhe
        tracks = {
            int(track_id): tuple(values)
            for track_id, values in tracks.items()
        }

        return watermark, tracks

    except Exception as e:
        print(f"Errore lettura watermark: {e}")
        return None, {}


def save_state(watermark, last_detections):

    data = {
        "watermark": watermark.isoformat(),
        "tracks": {
            str(track_id): list(values)
            for track_id, values in last_detections.items()
        }
    }

    # Scrittura prima su file temporaneo
    tmp_file = STATE_FILE + ".tmp"

    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=4)

    # sostituzione atomica del vecchio file
    os.replace(tmp_file, STATE_FILE)

load_dotenv()

""" 
producer = KafkaProducer(
bootstrap_servers=[
"kafka-0.vigimare.laurea.fi:9093",
"kafka-1.vigimare.laurea.fi:9093",
"kafka-2.vigimare.laurea.fi:9093"
],
value_serializer=lambda x: x.encode("utf-8")
) """

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
 
logging.getLogger("kafka").setLevel(logging. DEBUG)

# https://kafka-python.readthedocs.io/en/2.2.16/apidoc/KafkaProducer.html
producer = KafkaProducer(

    value_serializer=lambda x: x.encode("utf-8"),

    # Local Kafka
    #bootstrap_servers=["localhost:9092"],

    # Remote Kafka
    bootstrap_servers=["kafka-0.vigimare.laurea.fi:9093","kafka-1.vigimare.laurea.fi:9093","kafka-2.vigimare.laurea.fi:9093"],
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
    sasl_plain_username="rinac",
    sasl_plain_password="lahCiyVPrB5rT5F4TdeC",
    ssl_cafile = os.getenv("SSL_CAFILE")

 )

def create_topic(
    uc_no: str,
    live_historical_date: str,
    message_type: str,
    partner_service: str = None,
    postfix: str = None
) -> str:
    
    #UC<No>_<live/historical date>_<MessageType>_<Partner & Service Short Name>_<optional postfix>

    topic = f"UC{uc_no}_{live_historical_date}_{message_type}"

    if partner_service:
        topic += f"_{partner_service}"

    if postfix:
        topic += f"_{postfix}"

    return topic

def send_messages():

    # ==========================================================
    # INIZIALIZZAZIONE MODALITA'
    # ==========================================================

    if MODE_STATE == "test":

        # In TEST riparto sempre dalla data configurata
        watermark = TEST_START_TIME

        # In test azzero lo stato dei TrackID
        # così posso rieseguire sempre lo stesso replay
        last_detections = {}

        print("========================================")
        print("MODALITA': TEST")
        print(f"Partenza replay: {watermark}")
        print("========================================")

    elif MODE_STATE == "prod":

        # In PROD recupero lo stato persistente
        watermark, last_detections = load_state()

        # Primo avvio assoluto:
        # se non esiste ancora un watermark parto da ORA
        if watermark is None:
            watermark = datetime.now(timezone.utc)

            print("Primo avvio PROD.")
            print(f"Watermark inizializzato a: {watermark}")

        print("========================================")
        print("MODALITA': PROD")
        print(f"Watermark caricato: {watermark}")
        print(f"Track caricati: {last_detections}")
        print("========================================")

    else:
        raise ValueError(
            f"MODE_STATE non valido: {MODE_STATE}. "
            "Valori ammessi: 'test' oppure 'prod'."
        )

    while True:

        uc = "1.2"
        message_type = "Object"
        lhd = "live"
        partner_service_name = "RINA-C"
        SERVICE_NAME = "Sensors"

        KAFKA_TOPIC = create_topic(
            uc,
            lhd,
            message_type,
            partner_service_name
        )

        print(f"KAFKA_TOPIC : {KAFKA_TOPIC}")

        repo = InfluxRepository(
            INFLUX_URL,
            INFLUX_TOKEN,
            INFLUX_BUCKET
        )

        try:

            # ==========================================================
            # RANGE TEMPORALE
            # ==========================================================

            start_time = watermark

            if MODE_STATE == "test":

                # Replay storico:
                # avanzo sempre di 10 secondi
                end_time = start_time + timedelta(seconds=10)

            else:

                # Produzione:
                # non devo interrogare dati futuri
                now = datetime.now(timezone.utc)

                end_time = min(
                    start_time + timedelta(seconds=10),
                    now
                )

                # Se il watermark ha raggiunto il presente
                # aspetto il ciclo successivo
                if end_time <= start_time:

                    print(
                        f"Nessun nuovo intervallo disponibile. "
                        f"Watermark={watermark}"
                    )

                    repo.close()
                    time.sleep(5)
                    continue

            print(
                f"Range ricerca: "
                f"{start_time.isoformat()} -> "
                f"{end_time.isoformat()}"
            )

            detections = repo.get_detections(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )

            print(f"Detections trovate: {len(detections)}")

            # Ordino cronologicamente
            detections = sorted(
                detections,
                key=lambda d: d.GeneratedIn
            )

            maxMessages = 3
            sent_messages = 0

            # Tengo traccia dell'ultimo timestamp realmente elaborato
            latest_processed_time = watermark

            for detection in detections:

                detection_time = datetime.fromisoformat(
                    str(detection.GeneratedIn)
                )

                # ======================================================
                # TIMESTAMP GIA' ELABORATO
                # ======================================================

                if detection_time <= watermark:

                    print(
                        f"SKIP timestamp già processato: "
                        f"TrackID={detection.TrackID} "
                        f"time={detection.GeneratedIn}"
                    )

                    continue

                # ======================================================
                # CHIAVE STATO DELLA DETECTION
                # ======================================================

                detection_key = (
                    detection.Category,
                    detection.SourceType,
                    round(detection.newLat, 6),
                    round(detection.newLon, 6)
                )

                previous_key = last_detections.get(
                    detection.TrackID
                )

                # ======================================================
                # DETECTION INVARIATA
                # ======================================================

                if previous_key == detection_key:

                    print(
                        f"SKIP detection invariata: "
                        f"TrackID={detection.TrackID} "
                        f"time={detection.GeneratedIn} "
                        f"state={detection_key}"
                    )

                    latest_processed_time = detection_time

                    continue

                # ======================================================
                # DETECTION NUOVA O MODIFICATA
                # ======================================================

                print("=== DETECTION ===")

                print(f"generated_in          : {detection.GeneratedIn}")
                print(f"uuid                  : {detection.UUID}")
                print(f"latitude              : {detection.Latitude}")
                print(f"longitude             : {detection.Longitude}")
                print(
                    f"locationUncertainty   : "
                    f"{detection.LocationUncertainty}"
                )
                print(f"sourceType            : {detection.SourceType}")
                print(f"trackId               : {detection.TrackID}")
                print(f"category              : {detection.Category}")
                print(f"newLat                : {detection.newLat}")
                print(f"newLon                : {detection.newLon}")

                print("=====================")

                # ======================================================
                # CREAZIONE VIGIMARE OBJECT
                # ======================================================

                vigimare_object = create_vigimare_object(
                    legalname=SERVICE_NAME,
                    generated_in=detection.GeneratedIn,
                    uuid=detection.UUID,
                    latitude=detection.newLat,
                    longitude=detection.newLon,

                    # Uso il valore proveniente da Influx
                    location_uncertainty=detection.LocationUncertainty,

                    source_type=detection.SourceType,
                    track_id=detection.TrackID,
                    category=detection.Category,
                )

                # ======================================================
                # PAYLOAD KAFKA
                # ======================================================

                kafka_message = vigimare_object.to_string()

                print("")
                print(
                    "#######################################################################"
                )
                print("MESSAGGIO DA INVIARE A KAFKA")
                print(f"TOPIC   : {KAFKA_TOPIC}")
                print("PAYLOAD :")
                print(kafka_message)
                print(
                    "#######################################################################"
                )

                # ======================================================
                # INVIO KAFKA
                # ======================================================
                #
                # Riattiva questo blocco per effettuare l'invio reale:
                #
                # try:
                #
                #     future = producer.send(
                #         KAFKA_TOPIC,
                #         kafka_message
                #     )
                #
                #     metadata = future.get(timeout=10)
                #
                #     producer.flush()
                #
                #     print(
                #         "###############################################"
                #     )
                #     print("MESSAGGIO INVIATO CORRETTAMENTE A KAFKA")
                #     print(f"Topic     : {metadata.topic}")
                #     print(f"Partition : {metadata.partition}")
                #     print(f"Offset    : {metadata.offset}")
                #     print(
                #         "###############################################"
                #     )
                #
                # except Exception as kafka_error:
                #
                #     print(
                #         "###############################################"
                #     )
                #     print("ERRORE INVIO KAFKA")
                #     print(f"Topic  : {KAFKA_TOPIC}")
                #     print(f"Errore : {kafka_error}")
                #     print(
                #         "###############################################"
                #     )
                #
                #     raise

                # ======================================================
                # AGGIORNAMENTO STATO TRACK
                # ======================================================

                last_detections[detection.TrackID] = detection_key

                latest_processed_time = detection_time

                sent_messages += 1

                if sent_messages >= maxMessages:

                    print(
                        f"Raggiunto maxMessages={maxMessages}. "
                        f"Interrompo questo batch."
                    )

                    break

            # ==========================================================
            # AGGIORNAMENTO WATERMARK
            # ==========================================================

            if latest_processed_time > watermark:

                watermark = latest_processed_time

                print(
                    f"Watermark avanzato all'ultima detection: "
                    f"{watermark}"
                )

            else:

                # Non ho trovato detection nuove/processabili.
                # Avanzo fino alla fine della finestra interrogata.

                watermark = end_time

                print(
                    f"Nessuna nuova detection utile. "
                    f"Watermark avanzato a fine finestra: "
                    f"{watermark}"
                )

            # ==========================================================
            # PERSISTENZA
            # ==========================================================

            if MODE_STATE == "prod":

                # In produzione mantengo lo stato tra i restart
                save_state(
                    watermark,
                    last_detections
                )

                print(f"Watermark salvato: {watermark}")
                print(f"Stato TrackID: {last_detections}")

            else:

                # In TEST non modifico lo stato persistente PROD
                print(
                    f"[TEST] Watermark corrente: {watermark}"
                )

        except Exception as e:

            print(f"Errore durante elaborazione: {e}")

        finally:

            repo.close()

        time.sleep(5)

def handler(signum, frame):

    print("Bye")
    producer.close()
    exit(0)

signal.signal(signal.SIGINT, handler)

send_messages()