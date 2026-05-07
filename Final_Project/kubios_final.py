import json
import time
import network
import ubinascii
from umqtt.simple import MQTTClient
import local_calculation

values = local_calculation.heart()

SSID = "KME_751_G2"
PASSWORD = "riisipiirakka"
BROKER_IP = "192.168.2.253"
BROKER_PORT = 21883

REQUEST_TOPIC = b"kubios/request"
RESPONSE_TOPIC = b"kubios/response"
PATIENT_ADD = b"database/patients/add"
# PATIENT_LIST = b"database/patients/list"
PATIENT_RECORDS = b"database/records/add"

HISTORY_FILE = "kubios_history.json"
OUTPUT_FILE = "kubios_response.json"
TIMEOUT_MS = 15000

latest_response = None


# Callback for incoming MQTT messages
def mqtt_callback(topic, msg):
    global latest_response

    if topic != RESPONSE_TOPIC:
        return

    try:
        latest_response = json.loads(msg)
    except ValueError:
        latest_response = None


# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASSWORD)

        while not wlan.isconnected():
            time.sleep_ms(250)

    print("Wi-Fi connected:", wlan.ifconfig()[0])
    return wlan


# Get MAC address
def get_mac(wlan):
    mac_bytes = wlan.config("mac")
    return ubinascii.hexlify(mac_bytes).decode().upper()


# Build request payload
def build_payload(mac):
    return {
        "mac": mac,
        "type": "RRI",
        "data": values,
        "analysis": {"type": "readiness"}
    }


# Build a patient
name = input("Enter the patient name: ")


def build_patient(mac):
    return {
        "mac": mac,
        "patient_name": name
    }


# Save JSON to file
def save_to_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


def append_history(filename, data, patient_name):
    history = []

    try:
        with open(filename, "r") as f:
            history = json.load(f)
            if not isinstance(history, list):
                history = []
    except:
        history = []

    entry = {
        "timestamp": time.time(),
        "patient_name": patient_name,
        "mac": data["mac"],
        "rmssd": data["data"]["analysis"]["rmssd_ms"],
        "hr": data["data"]["analysis"]["mean_hr_bpm"],
        "sdnn": data["data"]["analysis"]["sdnn_ms"],
        "pns": data["data"]["analysis"]["pns_index"],
        "sns": data["data"]["analysis"]["sns_index"]
    }

    history.append(entry)

    with open(filename, "w") as f:
        json.dump(history, f)

    print("History updated:", filename)


# MAIN PROGRAM

# Connect to Wi-Fi
wlan = connect_wifi()

# Get MAC address
real_mac = get_mac(wlan)
print("Device MAC:", real_mac)

# Setup MQTT
client = MQTTClient(client_id=real_mac, server=BROKER_IP, port=BROKER_PORT)
client.set_callback(mqtt_callback)
client.connect()
client.subscribe(RESPONSE_TOPIC)

# Send request
payload = build_payload(real_mac)
print("Published to kubios/request")
print(json.dumps(payload))
patient = build_patient(real_mac)

client.publish(REQUEST_TOPIC, json.dumps(payload))
client.publish(PATIENT_ADD, json.dumps(patient))

# Wait for response
start = time.ticks_ms()

while True:
    client.check_msg()

    if latest_response and latest_response.get("mac") == real_mac:
        print("Response received:")
        print(json.dumps(latest_response))

        save_to_file(OUTPUT_FILE, latest_response)
        append_history(HISTORY_FILE, latest_response, name)

        print("Saved to file:", OUTPUT_FILE)
        print("Added to history:", HISTORY_FILE)

        break

    if time.ticks_diff(time.ticks_ms(), start) > TIMEOUT_MS:
        raise RuntimeError("Timeout waiting for response")

    time.sleep_ms(200)

# Disconnect
client.disconnect()
print("Done.")

if latest_response:
    print("rmssd:", latest_response["data"]["analysis"]["rmssd_ms"])
    print("hr:", latest_response["data"]["analysis"]["mean_hr_bpm"])
    print("sdnn:", latest_response["data"]["analysis"]["sdnn_ms"])
    print("pns:", latest_response["data"]["analysis"]["pns_index"])
    print("sns:", latest_response["data"]["analysis"]["sns_index"])


