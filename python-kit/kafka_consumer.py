import signal
from kafka import KafkaConsumer

KAFKA_TOPIC = "rina-test123"

# https://kafka-python.readthedocs.io/en/2.2.16/apidoc/KafkaConsumer.html
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    enable_auto_commit=True,
    value_deserializer=lambda x: x.decode("utf-8"),

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
