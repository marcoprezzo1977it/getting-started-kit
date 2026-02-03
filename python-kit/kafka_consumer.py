import signal
from kafka import KafkaConsumer

KAFKA_TOPIC = "test123"

# https://kafka-python.readthedocs.io/en/2.2.16/apidoc/KafkaConsumer.html
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    enable_auto_commit=True,
    value_deserializer=lambda x: x.decode("utf-8"),

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

def process_messages():
    print(f"Listening for messages on topic {KAFKA_TOPIC} ...")
    for message in consumer:
        xml = message.value
        print(f"Received message:\n{xml}\n")

available_topics = consumer.topics()
print(f"Found topics: {available_topics}")

def handler(signum, frame):
    print("Bye")
    consumer.close()
    exit (0)

signal.signal(signal.SIGINT, handler)

process_messages()
