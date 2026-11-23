# =========================================================================
# 5G WEARABLE ASSISTIVE DEVICE - ARDUINO APP LAB CLIENT
# Target: Arduino UNO Q (Linux + Python Runtime)
# Sensors: HC-SR04 Ultrasonic Sensor (via RouterBridge / Serial) + USB Forward Camera
# Uplink: 5G Mobile Hotspot -> Cloudflare Public Tunnel / UDP
# =========================================================================

import socket
import json
import time
import cv2
import threading

# --- 1. CONFIGURATION ---
# Set your public Cloudflare Tunnel URL to stream across independent networks
# (e.g. "https://your-tunnel.trycloudflare.com"). Leave empty to use local UDP.
CLOUDFLARE_URL   = "" 

# Local Network Fallback IP (only used if CLOUDFLARE_URL is empty)
EDGE_SERVER_IP   = "10.150.34.139"
VIDEO_PORT       = 5005     # UDP video stream to Edge Server
TELEMETRY_PORT   = 5006     # UDP distance telemetry to Edge Server
DOWNLINK_PORT    = 5007     # UDP incoming obstacle alerts from Edge Server

# Sensor defaults & state
current_distance_cm = 400.0
bridge_instance    = None
serial_device      = None
hardware_connected = False

def simulation_worker_thread():
    """
    Generates continuous test proximity values when physical sensors
    are not connected to the board.
    """
    global current_distance_cm
    sim_dist = 180.0
    step = -3.5
    print("🚀 [TEST SIMULATOR ACTIVE]: Generating continuous synthetic proximity telemetry.")
    while not hardware_connected:
        sim_dist += step
        if sim_dist <= 20.0:
            sim_dist = 20.0
            step = 4.0
        elif sim_dist >= 220.0:
            sim_dist = 220.0
            step = -3.5
        current_distance_cm = round(sim_dist, 1)
        time.sleep(0.1)

def init_hardware_link():
    """
    Connects to the MCU using Arduino UNO Q's native RouterBridge or Serial.
    """
    global bridge_instance, serial_device, hardware_connected

    # Method 1: Native Arduino UNO Q RouterBridge (MessagePack-RPC)
    try:
        from arduino.router_bridge import Bridge
        b = Bridge()
        if b.connect(timeout=3):
            print("🔌 [ARDUINO BRIDGE CONNECTED]: Successfully linked to MCU via native RouterBridge!")
            bridge_instance = b
            hardware_connected = True
            return
        else:
            print("ℹ️ RouterBridge connect timeout. Checking serial ports...")
    except ImportError:
        print("ℹ️ 'arduino.router_bridge' not in environment. Checking serial ports...")
    except Exception as e:
        print(f"ℹ️ RouterBridge init: {e}. Checking serial ports...")

    # Method 2: Serial Port Fallback
    import glob
    try:
        import serial
        potential_ports = (
            glob.glob("/dev/ttyACM*") + 
            glob.glob("/dev/ttyUSB*") + 
            glob.glob("/dev/ttyHS*") + 
            glob.glob("/dev/ttyMSM*") + 
            glob.glob("/dev/ttyS[0-9]*") + 
            [f"COM{i}" for i in range(1, 15)]
        )
        for port in potential_ports:
            try:
                ser = serial.Serial(port, 115200, timeout=0.1)
                print(f"🔌 [ARDUINO CONNECTED]: Successfully linked to MCU on {port}")
                serial_device = ser
                hardware_connected = True
                
                # Start background serial reading thread
                def serial_worker():
                    global current_distance_cm
                    while True:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line.startswith("{") and line.endswith("}"):
                                data = json.loads(line)
                                if "dist" in data:
                                    current_distance_cm = float(data["dist"])
                                elif "dist_cm" in data:
                                    current_distance_cm = float(data["dist_cm"])
                        except Exception:
                            time.sleep(0.02)
                
                t = threading.Thread(target=serial_worker, daemon=True)
                t.start()
                return
            except Exception:
                continue
    except ImportError:
        pass

    # If neither method succeeded, start the simulator
    print("ℹ️ Hardware link pending. Starting test simulator until MCU responds.")
    sim_t = threading.Thread(target=simulation_worker_thread, daemon=True)
    sim_t.start()

def read_ultrasonic_distance():
    """
    Returns the real-time distance from the physical Arduino MCU.
    """
    global current_distance_cm, bridge_instance
    if bridge_instance:
        try:
            val = bridge_instance.call("get_distance", timeout=0.15)
            if val is not None:
                current_distance_cm = float(val)
                return round(current_distance_cm, 1)
        except Exception:
            pass
    return round(current_distance_cm, 1)

def downlink_listener_thread(downlink_sock):
    """
    Background listener for 5G downlink alerts sent from the Edge Server.
    Logs incoming alerts received from the server.
    """
    print(f"👂 Downlink alert listener active on UDP port {DOWNLINK_PORT}")
    while True:
        try:
            data, addr = downlink_sock.recvfrom(2048)
            alert = json.loads(data.decode('utf-8'))
            alert_text = alert.get('text', 'Obstacle detected')
            print(f"\n🚨 [5G DOWNLINK RECEIVED]: {alert_text}")
        except Exception:
            time.sleep(0.01)

def main():
    print("==================================================")
    print("   5G WEARABLE ASSISTIVE DEVICE - ARDUINO UNO Q   ")
    print("==================================================")
    print(f"📡 Target Edge Server IP  : {EDGE_SERVER_IP}")
    print(f"🎥 Video Uplink Port      : {VIDEO_PORT} (UDP)")
    print(f"🧭 Telemetry Uplink Port  : {TELEMETRY_PORT} (UDP)")
    print(f"👂 Downlink Listen Port   : {DOWNLINK_PORT} (UDP)")
    print("==================================================")

    # 1. Connect to Hardware (RouterBridge or Serial)
    init_hardware_link()

    # 2. Setup UDP Sockets
    uplink_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    downlink_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        downlink_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        downlink_sock.bind(("0.0.0.0", DOWNLINK_PORT))
        listener = threading.Thread(target=downlink_listener_thread, args=(downlink_sock,), daemon=True)
        listener.start()
    except Exception as e:
        print(f"ℹ️ Downlink UDP socket notice: {e}. Continuing.")

    # 3. Initialize Camera
    print("📷 Initializing onboard camera (/dev/video0)...")
    cap = cv2.VideoCapture(0)
    has_camera = cap.isOpened()
    
    if has_camera:
        print("✅ Camera online!")
    else:
        print("⚠️ Camera not found on /dev/video0. Streaming ultrasonic telemetry.")

    print("\n🟢 5G Wearable Client running! Press Ctrl+C to terminate.\n")
    
    last_telemetry_time = 0

    try:
        while True:
            dist_cm = read_ultrasonic_distance()
            now = time.time()

            # --- 1. STREAM VIDEO OVER 5G UDP (:5005) ---
            if has_camera:
                ret, frame = cap.read()
                if ret:
                    frame_resized = cv2.resize(frame, (480, 320))
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
                    result, encimg = cv2.imencode('.jpg', frame_resized, encode_param)
                    if result:
                        payload = encimg.tobytes()
                        if len(payload) < 65000:
                            uplink_sock.sendto(payload, (EDGE_SERVER_IP, VIDEO_PORT))

            # --- 2. STREAM SENSOR TELEMETRY (Every 500ms / 2 Hz) ---
            if now - last_telemetry_time >= 0.5:
                # Path A: Cloudflare Public Tunnel (Works across two independent networks!)
                if CLOUDFLARE_URL and CLOUDFLARE_URL.strip():
                    try:
                        import urllib.request
                        clean_url = CLOUDFLARE_URL.strip().rstrip('/')
                        req_url = f"{clean_url}/api/telemetry?dist={dist_cm:.1f}"
                        req = urllib.request.Request(req_url, headers={"User-Agent": "5G_Wearable_UNO_Q"})
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            pass
                    except Exception:
                        pass
                
                # Path B: Local UDP Socket (Local Hotspot / LAN fallback)
                else:
                    telemetry = {
                        "ultrasonic_cm": dist_cm,
                        "timestamp": now
                    }
                    payload_json = json.dumps(telemetry).encode('utf-8')
                    try:
                        uplink_sock.sendto(payload_json, (EDGE_SERVER_IP, TELEMETRY_PORT))
                    except Exception:
                        pass

                last_telemetry_time = now
                if now - getattr(main, "_last_telemetry_print", 0) >= 2.0:
                    main._last_telemetry_print = now
                    dest = "Cloudflare Tunnel" if (CLOUDFLARE_URL and CLOUDFLARE_URL.strip()) else f"UDP {EDGE_SERVER_IP}:{TELEMETRY_PORT}"
                    print(f"📡 [5G Telemetry ➔ {dest}] Ultrasonic: {dist_cm:.1f} cm", flush=True)

            time.sleep(0.04) # ~25 FPS

    except KeyboardInterrupt:
        print("\nStopping Wearable Client...")
    finally:
        if has_camera:
            cap.release()
        uplink_sock.close()
        downlink_sock.close()

if __name__ == "__main__":
    main()
