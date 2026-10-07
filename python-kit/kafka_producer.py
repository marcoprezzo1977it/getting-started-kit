import signal
import time
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
KAFKA_TOPIC = "rina-test123"

""" 
producer = KafkaProducer(
bootstrap_servers=[
"kafka-0.vigimare.laurea.fi:9093",
"kafka-1.vigimare.laurea.fi:9093",
"kafka-2.vigimare.laurea.fi:9093"
],
value_serializer=lambda x: x.encode("utf-8")
) """

# https://kafka-python.readthedocs.io/en/2.2.16/apidoc/KafkaProducer.html
""" producer = KafkaProducer(
    value_serializer=lambda x: x.encode("utf-8"),

    # Local Kafka
    #bootstrap_servers=["localhost:9092"],

    # Remote Kafka
    bootstrap_servers=["kafka-0.vigimare.laurea.fi:9093","kafka-1.vigimare.laurea.fi:9093","kafka-2.vigimare.laurea.fi:9093"],
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
    sasl_plain_username="rinac",
    sasl_plain_password="lahCiyVPrB5rT5F4TdeC",
    ssl_cafile=None,
 )
 """ 
""" def send_messages():
    while True:
        # Creating a vigimare vessel with some randomized values
        vigimare_vessel = create_vigimare_vessel(
            legalname=SERVICE_NAME,
            generated_in=None,
            uuid=None,  # Will be generated
            latitude=59.3293 + round(random.uniform(-1.0, 1.0), 6),
            longitude=18.0686 + round(random.uniform(-1.0, 1.0), 6),
            name="Titanic",
            cog=90.0,
            heading=85.0 + round(random.uniform(-1.0, 1.0), 6),
            speed=12.5 + round(random.uniform(-1.0, 1.0), 6),
            breadth=5,
            call_sign="ABCD",
            depth=1.8,
            draught=1.8,
            length=15.0,
            mmsi=265513270,
            navigational_status="UnderWayUsingEngine",
            ais_ship_type=50,
            source_type="AIS",
        )
        # Send message to Kafka
        producer.send(KAFKA_TOPIC, vigimare_vessel.to_string())
        print(f"Sent message to topic {KAFKA_TOPIC}:\n{vigimare_vessel}\n")
        time.sleep(5)  # Sleep for 5 seconds to simulate real-time updates
 """
def send_messages():

        while True:

            repo = InfluxRepository(
                INFLUX_URL,
                INFLUX_TOKEN,
                INFLUX_BUCKET
            )

            print(f"INFLUX_URL={INFLUX_URL}")
            print(f"INFLUX_TOKEN={INFLUX_TOKEN}")
            print(f"INFLUX_BUCKET={INFLUX_BUCKET}")

            detections = repo.get_detections()

            print(f"Detections trovate: {len(detections)}")

            for detection in detections:

                print("=== DETECTION ===")
                print(f"generated_in          : {detection.GeneratedIn}")
                print(f"uuid                  : {detection.UUID}")
                print(f"latitude              : {detection.Latitude}")
                print(f"longitude             : {detection.Longitude}")
                print(f"locationUncertainty   : {detection.LocationUncertainty}")
                print(f"sourceType            : {detection.SourceType}")
                print(f"trackId               : {detection.TrackID}")
                print(f"category              : {detection.Category}")
                print("=================")

                vigimare_object = create_vigimare_object(
                    legalname=SERVICE_NAME,
                    generated_in=detection.GeneratedIn,
                    uuid=detection.UUID,
                    latitude=detection.Latitude,
                    longitude=detection.Longitude,
                    location_uncertainty=detection.LocationUncertainty,
                    source_type=detection.SourceType,
                    track_id=detection.TrackID,
                    category=detection.Category,
                )

                # producer.send(KAFKA_TOPIC, vigimare_object.to_string())

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
