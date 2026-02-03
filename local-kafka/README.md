# Local Kafka

This folder contains configuration to setup a simple local Kafka server that you may use to test producing and consuming messages. In addition to the Kafka server, there is also a web-UI for easy inspection of Kafka topics and messages.

## Prerequisites

Running the local Kafka server requires Docker and Docker Compose. Make sure you have them installed on the machine.

## Usage

You start the local kafka server and web-UI with the following command:

```bash
docker compose up -d
```

The web-UI is accessible at http://localhost:8080

You can see the status of the Docker containers by issuing the following command:

```bash
docker ps
```

The Docker containers can be stopped with the following command:

```bash
docker compose down
```

#### Quick-guide to the Kafka web-UI

Topics and messages in the Kafka server can be inspected using the Kafka web-UI in the following way:

1. Select "Topics" in the left side panel
2. Click on a topic in the list of topics
3. Select "Messages" tab in the row at the top of the page
4. Click the + sign for a message you want to inspect

## Configuration

The Kafka server can be connected to, by producers and consumers of messages, on `localhost:9092`.

The Kafka server has been configured to remove messages after 15 minutes. I.e. each message remain on the server for only 15 minutes. This duration can be adjusted in the `docker-compose.yaml` file, where it says `KAFKA_LOG_RETENTION_MINUTES`.