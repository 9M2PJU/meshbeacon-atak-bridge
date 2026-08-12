import os
import json
import socket
import logging
import datetime
from paho.mqtt import client as mqtt_client

# Configuration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "hub/event")
ATAK_IP = os.environ.get("ATAK_IP", "239.2.3.1") # Default multicast IP for ATAK
ATAK_PORT = int(os.environ.get("ATAK_PORT", 4242))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MeshBeacon-ATAK-Bridge")

# Create UDP socket for CoT
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def generate_cot_xml(device_id, lat, lon):
    now = datetime.datetime.utcnow()
    stale = now + datetime.timedelta(minutes=10)
    
    time_fmt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    stale_fmt = stale.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Simple CoT for a friendly ground unit
    cot = f"""<?xml version="1.0" standalone="yes"?>
<event version="2.0" uid="{device_id}" type="a-f-G-U-C" time="{time_fmt}" start="{time_fmt}" stale="{stale_fmt}" how="m-g">
    <point lat="{lat}" lon="{lon}" hae="0" ce="9999999.0" le="9999999.0"/>
    <detail>
        <contact callsign="{device_id}"/>
        <remarks>Forwarded by MeshBeacon Bridge</remarks>
    </detail>
</event>"""
    return cot

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        payload = data.get("payload", {})
        
        device_id = payload.get("DeviceID", "UnknownDevice")
        
        # MeshBeacon typically sends lat/lon in GPS events.
        # Fallbacks included to handle different potential payload structures.
        lat = payload.get("latitude") or payload.get("lat")
        lon = payload.get("longitude") or payload.get("lon")
        
        if lat is not None and lon is not None:
            logger.info(f"Received GPS for {device_id} -> Lat: {lat}, Lon: {lon}")
            cot_xml = generate_cot_xml(device_id, lat, lon)
            
            # Send via UDP to ATAK or TAK Server
            udp_socket.sendto(cot_xml.encode('utf-8'), (ATAK_IP, ATAK_PORT))
            logger.info(f"Forwarded CoT to ATAK ({ATAK_IP}:{ATAK_PORT})")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main():
    logger.info("Starting MeshBeacon to ATAK Bridge...")
    client = mqtt_client.Client("meshbeacon-atak-bridge")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Exiting...")
        udp_socket.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
