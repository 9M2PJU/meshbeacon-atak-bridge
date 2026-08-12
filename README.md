# MeshBeacon to ATAK Bridge

A lightweight Python microservice that listens to MeshBeacon's MQTT broker (`hub/event`), extracts incoming GPS coordinates from LoRa devices, formats them into Cursor-on-Target (CoT) XML, and broadcasts them via UDP to ATAK (Android Team Awareness Kit) devices or TAK Servers.

## Features
- Connects directly to MeshBeacon's Mosquitto broker.
- Translates JSON LoRa payloads to CoT XML on-the-fly.
- Supports ATAK UDP Multicast (`239.2.3.1`) out of the box, or unicast to a dedicated TAK server.

## Installation with Docker

1. Clone this repository next to your `meshbeacon` deployment.
2. Edit `docker-compose.yml` to ensure `MQTT_BROKER` points to your MeshBeacon MQTT container IP (or Docker DNS name).
3. Run it:
```bash
docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER` | localhost | The IP or hostname of your MeshBeacon MQTT broker. |
| `MQTT_PORT` | 1883 | The MQTT port. |
| `MQTT_TOPIC` | hub/event | The topic to listen for incoming radio events. |
| `ATAK_IP` | 239.2.3.1 | The IP to send CoT XML to. Use `239.2.3.1` for ATAK multicast, or the IP of your TAK Server. |
| `ATAK_PORT` | 4242 | The UDP port ATAK is listening on. |

## How it works
This bridge subscribes to `hub/event`. When MeshBeacon's radios (ClusterDuck/MamaDuck) send GPS data, the bridge parses the `lat` and `lon` fields. It immediately constructs an ATAK `<event>` with `type="a-f-G-U-C"` (friendly ground unit), injects the callsign, and fires it over UDP so it appears live on commanders' maps in the field.
