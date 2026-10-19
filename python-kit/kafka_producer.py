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

        while True:

            uc = "1.2"

            test = "live_Object_RINA-C"

            message_type = "Object"

            lhd = "live" #datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            partner_service_name = "RINA-C"
            #UC<No>_<live/historical date>_<MessageType>_<Partner & Service Short Name>_<optional postfix>

            KAFKA_TOPIC = create_topic(uc,lhd,message_type,partner_service_name)

            print("KAFKA_TOPIC : {KAFKA_TOPIC}")

            repo = InfluxRepository(
                INFLUX_URL,
                INFLUX_TOKEN,
                INFLUX_BUCKET
            )

            SERVICE_NAME = "Sensors"

            detections = repo.get_detections()

            maxMessages = 3
            
            print(f"Detections trovate: {len(detections)}")

            for detection in detections[:maxMessages]:

                print("=== DETECTION ===")
                
                print(f"generated_in          : {detection.GeneratedIn}")
                print(f"uuid                  : {detection.UUID}")
                print(f"latitude              : {detection.Latitude}")
                print(f"longitude             : {detection.Longitude}")
                print(f"locationUncertainty   : {detection.LocationUncertainty}")
                print(f"sourceType            : {detection.SourceType}")
                print(f"trackId               : {detection.TrackID}")
                print(f"category              : {detection.Category}")
                print(f"newLat                : {detection.newLat}")
                print(f"newLon                : {detection.newLon}")
                print("=================")

                vigimare_object = create_vigimare_object(
                    legalname=SERVICE_NAME,
                    generated_in=detection.GeneratedIn,
                    uuid=detection.UUID,
                    latitude=detection.newLat,
                    longitude=detection.newLon,
                    location_uncertainty=LOCATION_UNCERTAINLY,  # valore fisso AM 20261016
                    source_type=detection.SourceType,
                    track_id=detection.TrackID,
                    category=detection.Category,
                )

                print("=== VIGIMARE OBJECT ===")
                print(vigimare_object)

                print("ATTRIBUTI:")
                print(vars(vigimare_object))
                print("========================")

#                producer.send(KAFKA_TOPIC, vigimare_object.to_string())

                print(
                    f"Sent message to topic {KAFKA_TOPIC}:\n"
                    f"{vigimare_object}\n"
                )

            repo.close()

            time.sleep(5)

def handler(signum, frame):
    print("Bye")
    producer.close()
    exit (0)

signal.signal(signal.SIGINT, handler)

send_messages()
