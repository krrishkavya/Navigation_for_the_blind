# =========================================================================
# 5G WEARABLE ASSISTIVE DEVICE - LINUX MPU CLIENT (ARDUINO UNO Q)
# Communicates with:
#   1. STM32 MCU via RouterBridge RPC / Serial (Live HC-SR04 Ultrasonic)
#   2. USB Camera (/dev/video*) with deep hardware diagnostic reporting
#   3. Edge Server on Laptop via Cloudflare Tunnel / UDP
# =========================================================================

import os
# Silence internal OpenCV / GStreamer C++ warnings when probing devices
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import socket
import json
import time
import cv2
import threading

if hasattr(cv2, "setLogLevel"):
    cv2.setLogLevel(0)

# --- 1. NETWORK CONFIGURATION ---
# Paste your public Cloudflare Tunnel URL to stream across independent networks
# (e.g. "https://your-tunnel.trycloudflare.com"). Leave empty to use local UDP.
CLOUDFLARE_URL   = "" 

# Local Network Fallback IP (only used if CLOUDFLARE_URL is empty)
EDGE_SERVER_IP   = "192.168.0.108"
VIDEO_PORT       = 5005     # UDP video stream to Edge Server
TELEMETRY_PORT   = 5006     # UDP distance telemetry to Edge Server
DOWNLINK_PORT    = 5007     # UDP incoming obstacle alerts from Edge Server

# Global hardware state (Pure Real-World Hardware - Zero Synthetic Noise)
current_distance_cm = 400.0
bridge_instance     = None
serial_device       = None
hardware_connected  = False

# -------------------------------------------------------------------------
# Connect to the STM32 MCU (RouterBridge Primary, Serial Fallback)
# -------------------------------------------------------------------------
def init_hardware_link():
    global bridge_instance, serial_device, hardware_connected

    # Method 1: Arduino UNO Q Native RouterBridge (MessagePack-RPC over IPC)
    try:
        from arduino.router_bridge import Bridge
        b = Bridge()
        if b.connect(timeout=3):
            print("🔌 [HARDWARE LINK]: Successfully linked to STM32 MCU via RouterBridge!")
            bridge_instance = b
            hardware_connected = True
            return
        else:
            print("ℹ️ RouterBridge connect timeout. Attempting serial fallback...")
    except ImportError:
        print("ℹ️ 'arduino.router_bridge' not in environment. Attempting serial fallback...")
    except Exception as e:
        print(f"ℹ️ RouterBridge connection note: {e}. Attempting serial fallback...")

    # Method 2: Serial Port Fallback (Reads JSON {"dist": XX.X} directly)
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
                print(f"🔌 [HARDWARE LINK]: Linked to STM32 MCU on Serial port {port}")
                serial_device = ser
                hardware_connected = True
                
                # Dedicated thread to keep serial buffer drained and distance fresh
                def serial_worker():
                    global current_distance_cm
                    while True:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line.startswith("{") and line.endswith("}"):
                                data = json.loads(line)
                                if "dist" in data:
                                    current_distance_cm = float(data["dist"])
                        except Exception:
                            time.sleep(0.02)
                
                threading.Thread(target=serial_worker, daemon=True).start()
                return
            except Exception:
                continue
    except Exception:
        pass

    if not hardware_connected:
        print("⚠️ [HARDWARE NOTICE]: Waiting for STM32 MCU heartbeat...")

# -------------------------------------------------------------------------
# Read Real Ultrasonic Distance from MCU
# -------------------------------------------------------------------------
def read_ultrasonic_distance():
    global current_distance_cm, bridge_instance
    if bridge_instance:
        try:
            # Query the live distance from the get_distance function in sketch.ino
            val = bridge_instance.call("get_distance", timeout=0.20)
            if val is not None:
                current_distance_cm = float(val)
                return round(current_distance_cm, 1)
        except Exception:
            pass  # Fall through to last recorded distance
            
    return round(current_distance_cm, 1)

# -------------------------------------------------------------------------
# Comprehensive Hot-Pluggable Camera Detector with Raw Kernel Diagnostics
# -------------------------------------------------------------------------
def detect_camera():
    import glob, subprocess

    devices = sorted(glob.glob("/dev/video*"))
    
    # Periodic diagnostic print to inform the user exactly what the OS sees
    now = time.time()
    if now - getattr(detect_camera, "_last_diag_time", 0) >= 5.0:
        detect_camera._last_diag_time = now
        
        # 1. Enumerate video nodes and their driver names from sysfs
        video_info = []
        for dev in devices:
            node_name = os.path.basename(dev)
            name_file = f"/sys/class/video4linux/{node_name}/name"
            label = dev
            if os.path.exists(name_file):
                try:
                    with open(name_file, "r") as f:
                        label = f"{dev} ({f.read().strip()})"
                except Exception:
                    pass
            video_info.append(label)

        # 2. Enumerate USB devices from sysfs (zero external binaries required)
        usb_devices = []
        for prod_path in glob.glob("/sys/bus/usb/devices/*/product"):
            try:
                dev_dir = os.path.dirname(prod_path)
                with open(prod_path, "r") as f:
                    prod = f.read().strip()
                mfg = ""
                mfg_path = os.path.join(dev_dir, "manufacturer")
                if os.path.exists(mfg_path):
                    with open(mfg_path, "r") as f:
                        mfg = f.read().strip()
                usb_devices.append(f"{mfg} {prod}".strip())
            except Exception:
                pass

        # 3. Check and attempt to enforce USB Host Mode Role
        roles = []
        for role_path in glob.glob("/sys/class/usb_role/*/role"):
            try:
                with open(role_path, "r+") as f:
                    curr = f.read().strip()
                    roles.append(curr)
                    if curr != "host":
                        try:
                            f.seek(0)
                            f.write("host")
                            roles.append("-> switched to host")
                        except Exception as write_err:
                            roles.append(f"(write err: {write_err})")
            except Exception:
                pass

        print(f"🔍 [HARDWARE SCAN]: Video nodes: {video_info if video_info else 'None'}")
        print(f"   ↳ USB Bus Devices : {', '.join(usb_devices) if usb_devices else 'No USB devices enumerated by kernel'}")
        print(f"   ↳ USB Port Role   : {roles if roles else 'Unknown'}")

    # Exclude internal Qualcomm Venus encoder/decoder nodes (video0, video1)
    # External UVC webcams always enumerate on video2, video3, etc.
    camera_candidates = [d for d in devices if d not in ("/dev/video0", "/dev/video1")]
    if not camera_candidates:
        # Fallback to checking video2 directly
        camera_candidates = ["/dev/video2", "/dev/video3"]

    for dev in camera_candidates:
        suffix = dev.replace("/dev/video", "")
        dev_idx = int(suffix) if suffix.isdigit() else 2

        # Try opening via V4L2 backend and CAP_ANY
        open_attempts = [
            (dev_idx, getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)),
            (dev_idx, cv2.CAP_ANY),
            (dev, getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)),
            (dev, cv2.CAP_ANY)
        ]

        for target, backend in open_attempts:
            try:
                cap = cv2.VideoCapture(target, backend) if isinstance(target, int) else cv2.VideoCapture(target)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        print(f"📷 [CAMERA ONLINE]: Successfully streaming video from {dev} (Index {dev_idx})!")
                        return cap
                    cap.release()
            except Exception:
                continue

    return None

# -------------------------------------------------------------------------
# Main Execution Loop
# -------------------------------------------------------------------------
def main():
    print("==================================================")
    print("   5G WEARABLE ASSISTIVE DEVICE - ARDUINO UNO Q   ")
    print("==================================================")
    print(f"📡 Target Edge Server IP  : {EDGE_SERVER_IP}")
    print(f"🎥 Video Uplink Port      : {VIDEO_PORT} (UDP)")
    print(f"🧭 Telemetry Uplink Port  : {TELEMETRY_PORT} (UDP)")
    print(f"👂 Downlink Listen Port   : {DOWNLINK_PORT} (UDP)")
    print("==================================================")

    # 1. Establish hardware link with STM32 MCU
    init_hardware_link()

    # 2. Setup UDP transmission sockets
    uplink_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    downlink_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        downlink_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        downlink_sock.bind(("0.0.0.0", DOWNLINK_PORT))
        
        def downlink_worker():
            while True:
                try:
                    data, _ = downlink_sock.recvfrom(2048)
                    alert = json.loads(data.decode('utf-8'))
                    print(f"\n🚨 [SERVER ALERT]: {alert.get('text', 'Obstacle warning')}")
                except Exception:
                    time.sleep(0.01)
                    
        threading.Thread(target=downlink_worker, daemon=True).start()
    except Exception as e:
        print(f"ℹ️ Downlink UDP socket info: {e}. Continuing.")

    # 3. Detect onboard/USB camera
    cap = detect_camera()
    last_camera_retry_time = 0
    last_telemetry_time = 0

    print("\n🟢 5G Wearable Client running! Press Ctrl+C to terminate.\n")

    try:
        while True:
            now = time.time()
            dist_cm = read_ultrasonic_distance()

            # --- 1. CAMERA STREAMING WITH AUTO-RECONNECT ---
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Resize to 480x320 and encode as JPEG (Quality 65) for low latency
                    frame_resized = cv2.resize(frame, (480, 320))
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
                    result, encimg = cv2.imencode('.jpg', frame_resized, encode_param)
                    if result:
                        payload = encimg.tobytes()
                        if len(payload) < 65000:
                            uplink_sock.sendto(payload, (EDGE_SERVER_IP, VIDEO_PORT))
                else:
                    # Camera lost connection
                    print("⚠️ Camera frame drop. Re-detecting camera...")
                    cap.release()
                    cap = None
            else:
                # Hot-plug detection: periodically check for newly plugged USB camera
                if now - last_camera_retry_time >= 3.0:
                    last_camera_retry_time = now
                    cap = detect_camera()

            # --- 2. SENSOR TELEMETRY UPLINK (Every 500ms / 2 Hz) ---
            if now - last_telemetry_time >= 0.5:
                # Path A: Cloudflare Public Tunnel (Cellular / Independent Networks)
                if CLOUDFLARE_URL and CLOUDFLARE_URL.strip():
                    try:
                        import urllib.request
                        clean_url = CLOUDFLARE_URL.strip().rstrip('/')
                        req_url = f"{clean_url}/api/telemetry?dist={dist_cm:.1f}"
                        req = urllib.request.Request(req_url, headers={"User-Agent": "5G_Wearable_UNO_Q"})
                        with urllib.request.urlopen(req, timeout=0.8) as resp:
                            pass
                    except Exception:
                        pass
                
                # Path B: Direct Local UDP Socket
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
                    cam_status = "Online" if (cap is not None and cap.isOpened()) else "Standby (Detecting USB Camera...)"
                    print(f"📡 [5G Telemetry ➔ {dest}] Distance: {dist_cm:.1f} cm | Camera: {cam_status}", flush=True)

            time.sleep(0.04) # ~25 FPS loop pace

    except KeyboardInterrupt:
        print("\nStopping Wearable Client...")
    finally:
        if cap is not None:
            cap.release()
        uplink_sock.close()
        downlink_sock.close()

if __name__ == "__main__":
    main()
