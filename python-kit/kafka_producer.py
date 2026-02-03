import random
import signal
import time
from kafka import KafkaProducer
from utils.helper_functions import create_vigimare_vessel

SERVICE_NAME = "My vigimare vessel producing service"
KAFKA_TOPIC = "test123"

# https://kafka-python.readthedocs.io/en/2.2.16/apidoc/KafkaProducer.html
producer = KafkaProducer(
    value_serializer=lambda x: x.encode("utf-8"),

    # Local Kafka
    bootstrap_servers=["localhost:9092"],

    # Remote Kafka
    # bootstrap_servers=["....", "....", "...."],
    # security_protocol="SASL_SSL",
    # sasl_mechanism="PLAIN",
    # sasl_plain_username="....",
    # sasl_plain_password="....",
    # ssl_cafile="cert-chain.pem",
)

def send_messages():
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

def handler(signum, frame):
    print("Bye")
    producer.close()
    exit (0)

signal.signal(signal.SIGINT, handler)

send_messages()
