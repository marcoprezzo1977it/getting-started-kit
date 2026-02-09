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

## Optional: add additional external Kafka server to the Kafka UI frontend
execute all commands in the `local-kafka` folder

Create a `.env` file with the following keys and fill in the values, keystorePassword can be anything
``` sh
BOOTSTRAP=<kafka bootstrap servers separated by ,>
SASL_USER=<username>
SASL_PASS=<password>
KEYSTORE_PW=<keystorePassword>
```

### Create a local keystore for the server root certificate:
This step only needs to be executed once to create a keystore with the servers root CA.
This needs openssl to downlaod the CA and java installed for the keystore creation.
Apply the variables to current shell:
``` sh
source .env 
```
Pick one broker and look at its certificate chain 
``` sh
openssl s_client -connect $(echo $BOOTSTRAP | cut -d, -f1) -servername $(echo $BOOTSTRAP | cut -d, -f1 | cut -d: -f1) -showcerts </dev/null 2>/dev/null | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/{print > "chain.pem"}' 
```
Split the chain into individual files (cert-00.pem, cert-01.pem …) 
```sh
csplit -s -f cert- -b %02d.pem chain.pem '/-----BEGIN CERTIFICATE-----/' '{*}'
``` 
The last cert in the chain is the CA → import it to a (java) keystore
``` sh
keytool -importcert -alias kafka-ca -file $(ls cert-* | tail -n1) -keystore truststore.jks -storepass "$KEYSTORE_PW" -noprompt
```
cleanup 
``` sh
rm *.pem
```

### Update docker-compose
in `docker-compose.yaml` uncomment additional `KAFKA_CLUSTERS_1_*` properties and the truststore volume. 
Now the docker copmose can be used as described above and KafkaUI also shows the external Server.
