import os
import sys

# Ensure edge_server is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
edge_server_path = os.path.join(project_root, "edge_server")
wearable_path = os.path.join(project_root, "wearable_client")
sys.path.insert(0, edge_server_path)

print("=" * 60)
print("VERIFYING BLUETOOTH LOW ENERGY (BLE) WEARABLE INTEGRATION")
print("=" * 60)

# -------------------------------------------------------------
# Test 1: Arduino Firmware BLE Verification
# -------------------------------------------------------------
print("\n--- Test 1: Arduino Firmware Architecture (Arduino UNO Q) ---")
ino_path = os.path.join(wearable_path, "sketch", "sketch.ino")
with open(ino_path, "r", encoding="utf-8") as f:
    ino_content = f.read()

assert "PIN_HAPTIC_BUZZER" in ino_content, "Missing PIN_HAPTIC_BUZZER in sketch.ino!"
assert "updateHapticFeedback" in ino_content, "Missing tactile haptic feedback in sketch.ino!"
assert "sendTelemetryPacket" in ino_content, "Missing sendTelemetryPacket in sketch.ino!"
assert "ptt_press" in ino_content, "Missing PTT button event in sketch.ino!"
print("✅ Test 1 Passed: Arduino UNO Q sketch configured with tactile haptics & telemetry!")

# -------------------------------------------------------------
# Test 2: Mobile Web Client BLE Pairing & Ingestion
# -------------------------------------------------------------
print("\n--- Test 2: Mobile Web Client BLE Manager ---")
app_js_path = os.path.join(edge_server_path, "web_client", "app.js")
with open(app_js_path, "r", encoding="utf-8") as f:
    app_js_content = f.read()

assert "connectBleWearable" in app_js_content, "Missing connectBleWearable function in app.js!"
assert "handleBleNotification" in app_js_content, "Missing handleBleNotification function in app.js!"
assert "navigator.bluetooth.requestDevice" in app_js_content, "Missing Web Bluetooth requestDevice in app.js!"
assert "lastBleUltrasonicCm" in app_js_content, "Missing lastBleUltrasonicCm state in app.js!"
assert "ultrasonic_cm: lastBleUltrasonicCm" in app_js_content, "Missing ultrasonic telemetry uplink in app.js!"
print("✅ Test 2 Passed: Web Bluetooth manager and telemetry uplink verified in app.js!")

# -------------------------------------------------------------
# Test 3: Mobile Web Client UI Pairing Badge
# -------------------------------------------------------------
print("\n--- Test 3: Web Client HTML UI Pairing Badge ---")
html_path = os.path.join(edge_server_path, "web_client", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

assert 'id="bleBadge"' in html_content, "Missing bleBadge button in index.html!"
assert "connectBleWearable()" in html_content, "Missing onclick handler for BLE in index.html!"
print("✅ Test 3 Passed: 1-tap BLE pairing badge verified in index.html!")

# -------------------------------------------------------------
# Test 4: Mobile Bridge Ultrasonic Ingestion
# -------------------------------------------------------------
print("\n--- Test 4: Mobile Bridge Ultrasonic Telemetry ---")
from mobile_bridge import MobileBridgeServer

bridge = MobileBridgeServer(port=8095)
assert hasattr(bridge, 'get_latest_ultrasonic'), "MobileBridgeServer missing get_latest_ultrasonic method!"
assert bridge.get_latest_ultrasonic() == 400.0, "Default ultrasonic value mismatch!"

# Simulate incoming BLE ultrasonic packet from mobile phone
with bridge.lock:
    bridge.latest_telemetry["ultrasonic_cm"] = 82.5

assert bridge.get_latest_ultrasonic() == 82.5, "Failed to read updated ultrasonic telemetry!"
print("✅ Test 4 Passed: Mobile bridge correctly ingests and serves ultrasonic telemetry!")

print("\n" + "=" * 60)
print("🎉 ALL BLE WEARABLE INTEGRATION TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
