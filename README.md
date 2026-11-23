# 5G Assistive Wearable Navigation & Collision Avoidance

An autonomous assistive navigation system designed for visually impaired pedestrians. The system integrates a wearable chest camera, ultrasonic sensor (10 Hz), a high-speed Edge AI server, and an accessible mobile web companion over 5G.

---

## 1. What the Project Does

The system performs three core roles in real time:
1. **Guide (Turn-by-Turn Pedestrian Navigation)**: Computes authentic walking paths via OpenStreetMap/OSRM foot routers, guides the user safely to the footpath with an initial approach phase, delivers clock-face directional cues, and dynamically switches to shorter routes if an optimized path emerges.
2. **Protect (Proactive Obstacle & Collision Warnings)**: Combines YOLOv8 real-time detection (restricted to genuine hazard classes) and on-demand MiDaS depth estimation with multi-frame object tracking (`ThreatTracker`). Calculates Time-To-Collision (TTC) and closing speed ($m/s$) to warn of fast-approaching vehicles and immediate hazards while staying quiet for stationary or retreating objects. The chest ultrasonic sensor provides independent near-field bumper protection (contact $\le 25\text{ cm}$).
3. **Recover (Off-Route & Signal Fail-Safes)**: Seamlessly reroutes if the user drifts off the path, warns when GPS accuracy drops or restores, and speaks locally on the phone if the 5G connection to the edge server drops.

---

## 2. Quick Start (Demo Mode)

### Step 1: Launch Edge Server
Run the one-click launcher from the project directory:
```bat
run_demo.bat
```
Alternatively, in PowerShell:
```powershell
.\.venv\Scripts\activate
python edge_server\server.py
```

### Step 2: Connect Phone Companion
1. When the server launches, a **QR code** is displayed on the screen and in the terminal.
2. Scan the QR code using your iPhone or Android camera to open the 5G web client (`https://...trycloudflare.com` or local Wi-Fi).
3. **Tap once anywhere on the phone screen** to unlock audio synthesis and enable motion/compass sensors.

### Step 3: Start Voice Navigation
- **Voice Command**: Press the screen button or say your destination (e.g. *"New SAC"* or *"Central Library"*). Spoken queries prompt a double-tap confirmation.
- **Terminal Simulator / Test**:
  ```powershell
  python edge_server\test_navigation_simulation.py "New SAC" --speed 1
  ```

---

## 3. Configuration Switches (`edge_server/navigation/nav_config.json`)

Key runtime toggles can be adjusted dynamically without recompiling:

| Setting Key | Default | Description |
| :--- | :--- | :--- |
| `laptop_speaks_alerts` | `true` | Allows the edge server laptop to speak obstacle alerts aloud for audience demonstrations. Set to `false` for earphone-only use. |
| `depth_on_demand` | `true` | Runs the heavy MiDaS depth estimator only when a recognized hazard is inside the walking corridor, boosting FPS by 2–3×. |
| `ttc_alerts_enabled` | `true` | Enables velocity tracking and Time-To-Collision (TTC) filtering for both vision threats and ultrasonic proximity. |
| `ttc_warning_s` | `3.0` | Maximum TTC threshold (seconds) for triggering obstacle warnings. |
| `ttc_critical_s` | `1.5` | Critical emergency stop threshold for immediate braking warnings. |
| `approach_gap_m` | `12.0` | Threshold to trigger the initial "walk to the path" approach phase before step maneuvers begin. |
| `reopt_enabled` | `true` | Enables event-driven route re-optimization for shorter walking alternatives. |

---

## 4. Known Technical Limitations

1. **GPS Satellite Masking**: Standard mobile GPS degrades indoors or under heavy concrete overhangs and dense tree canopies ($\text{accuracy} > 30\text{ m}$). The server warns with *"GPS signal weak"* and relies on dead-reckoning/last fix until signal recovers.
2. **Monocular Depth & Lighting**: Camera-based depth estimation requires ambient illumination. Under pitch-black conditions, the wearable relies primarily on the 10 Hz ultrasonic proximity sensor.
3. **Ultrasonic Beam Geometry**: The chest ultrasonic transducer has a $\sim 15^\circ$ beam cone; obstacles situated outside this field-of-view are covered by the wide-angle camera.
