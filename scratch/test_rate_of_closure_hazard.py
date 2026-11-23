"""
Automated Verification Suite: Rate-of-Closure Approaching Hazard Gating
Verifies the new dynamic collision flow:
1. Static Chair at 1.1m (User sitting at desk) -> SILENT (no spam)
2. Approaching Chair / Walking user (Distance closing in from 2.0m to 1.4m) -> ALERTS
3. Static Hand at 45cm on Ultrasonic sensor -> SILENT (no desk spam)
4. Hand moving toward Ultrasonic sensor (Distance closing in from 70cm to 45cm) -> ALERTS
5. Emergency contact bumper (<= 25cm) -> Immediate warning
6. Microphone recording active on phone -> ALL alerts muted so mic is clean
7. Cooldown verification: 3.0s warning cooldown, 2.0s critical cooldown
"""

import collections
import time

def simulate_pipeline(
    history_records,
    is_walking,
    obstacle_moving,
    user_speaking=False,
    last_alert_time=-999.0
):
    """
    Feeds a sequence of time-stepped readings through the Rate-of-Closure engine.
    history_records is a list of (timestamp, ultrasonic_cm, vision_threat_list)
    Returns list of alerts fired: [(timestamp, warning_msg, urgency, source)]
    """
    cooldown_warn = 3.0
    cooldown_crit = 2.0
    cooldown_immediate = 3.5
    
    ultra_history = collections.deque(maxlen=6)
    vision_history = collections.deque(maxlen=6)
    
    alerts_fired = []
    
    for now, current_ultra, valid_threats in history_records:
        alert_dispatched = False
        
        # 1. Track Ultrasonic Rate-of-Closure
        ultra_is_closing = False
        if current_ultra is not None and 2.0 <= current_ultra <= 250.0:
            ultra_history.append((current_ultra, now))
            if len(ultra_history) >= 3:
                old_u_dist, old_u_t = ultra_history[0]
                u_dt = now - old_u_t
                if 0.25 <= u_dt <= 1.5:
                    u_delta = current_ultra - old_u_dist
                    if u_delta <= -6.0:
                        ultra_is_closing = True

        # 2. Track Vision AI Rate-of-Closure
        vision_is_closing = False
        if valid_threats:
            p_dist = valid_threats[0]['distance']
            vision_history.append((p_dist, now))
            if len(vision_history) >= 3:
                old_v_dist, old_v_t = vision_history[0]
                v_dt = now - old_v_t
                if 0.25 <= v_dt <= 1.5:
                    v_delta = p_dist - old_v_dist
                    if v_delta <= -0.15:
                        vision_is_closing = True

        motion_active = (is_walking or obstacle_moving)

        # Layer 1: Ultrasonic
        if current_ultra is not None and 2.0 <= current_ultra <= 100.0:
            is_immediate_contact = (current_ultra <= 25.0)
            is_approaching_hazard = (ultra_is_closing and motion_active)
            
            if is_immediate_contact or is_approaching_hazard:
                is_ultra_critical = (current_ultra <= 50.0)
                active_cooldown = cooldown_immediate if is_immediate_contact else (
                    cooldown_crit if is_ultra_critical else cooldown_warn
                )
                
                if (now - last_alert_time) > active_cooldown and not user_speaking:
                    fused_name = "obstacle"
                    if valid_threats and valid_threats[0]['distance'] <= 2.2:
                        fused_name = valid_threats[0]['name']
                    urgency = "critical" if is_ultra_critical else "warning"
                    msg = f"Stop! {fused_name} {int(current_ultra)} centimeters"
                    last_alert_time = now
                    alert_dispatched = True
                    alerts_fired.append((now, msg, urgency, "ultrasonic"))

        # Layer 2: Vision AI
        if not alert_dispatched and valid_threats:
            primary = valid_threats[0]
            dist = primary['distance']
            p_name = primary['name']
            
            if dist <= 3.5:
                is_critical = (dist <= 1.5)
                closing_in = (vision_is_closing or ultra_is_closing)
                should_alert = closing_in and motion_active
                
                active_cooldown = cooldown_crit if is_critical else cooldown_warn
                cooldown_ready = (now - last_alert_time) > active_cooldown
                
                if should_alert and not user_speaking and cooldown_ready:
                    urgency = "critical" if is_critical else "warning"
                    msg = f"Stop! {p_name} {float(dist):.1f} meters" if is_critical else f"{p_name} ahead, {float(dist):.1f} meters"
                    last_alert_time = now
                    alerts_fired.append((now, msg, urgency, "vision"))

    return alerts_fired

def run_tests():
    passed = 0
    total = 0
    print("=" * 70)
    print("RUNNING RATE-OF-CLOSURE (APPROACHING HAZARD) VERIFICATION")
    print("=" * 70)

    # Test 1: Static Chair at 1.1m (User sitting at desk, nothing moving)
    total += 1
    stream = [
        (0.0, 400.0, [{'name': 'chair', 'distance': 1.10}]),
        (0.2, 400.0, [{'name': 'chair', 'distance': 1.10}]),
        (0.4, 400.0, [{'name': 'chair', 'distance': 1.11}]),
        (0.6, 400.0, [{'name': 'chair', 'distance': 1.09}]),
        (0.8, 400.0, [{'name': 'chair', 'distance': 1.10}]),
    ]
    alerts = simulate_pipeline(stream, is_walking=False, obstacle_moving=False)
    assert len(alerts) == 0, f"Test 1 Failed: Expected 0 alerts for static chair, got {alerts}"
    print(" [PASS] Test 1: Static chair at 1.1m while seated is 100% SILENT (No desk chatter)!")
    passed += 1

    # Test 2: Walking User approaching Chair (Distance closing in from 2.2m to 1.3m)
    total += 1
    stream = [
        (0.0, 400.0, [{'name': 'chair', 'distance': 2.20}]),
        (0.2, 400.0, [{'name': 'chair', 'distance': 1.95}]),
        (0.4, 400.0, [{'name': 'chair', 'distance': 1.70}]),
        (0.6, 400.0, [{'name': 'chair', 'distance': 1.45}]),
        (0.8, 400.0, [{'name': 'chair', 'distance': 1.20}]),
    ]
    alerts = simulate_pipeline(stream, is_walking=True, obstacle_moving=False)
    assert len(alerts) >= 1 and "chair" in alerts[0][1], f"Test 2 Failed: Expected alert for closing chair, got {alerts}"
    print(f" [PASS] Test 2: Walking user approaching chair fires alert: '{alerts[0][1]}'")
    passed += 1

    # Test 3: Static Hand at 45cm on Ultrasonic sensor (Stationary hand)
    total += 1
    stream = [
        (0.0, 45.0, []),
        (0.2, 45.2, []),
        (0.4, 44.9, []),
        (0.6, 45.1, []),
        (0.8, 45.0, []),
    ]
    alerts = simulate_pipeline(stream, is_walking=False, obstacle_moving=False)
    assert len(alerts) == 0, f"Test 3 Failed: Static hand at 45cm should not alert repeatedly, got {alerts}"
    print(" [PASS] Test 3: Static hand held at 45cm is SILENT (No siren loop)!")
    passed += 1

    # Test 4: Hand actively closing in on Ultrasonic sensor (70cm -> 35cm)
    total += 1
    stream = [
        (0.0, 70.0, []),
        (0.2, 60.0, []),
        (0.4, 48.0, []),
        (0.6, 36.0, []),
    ]
    alerts = simulate_pipeline(stream, is_walking=False, obstacle_moving=True) # hand moving
    assert len(alerts) >= 1 and alerts[0][3] == "ultrasonic", f"Test 4 Failed: Expected closing ultrasonic alert, got {alerts}"
    print(f" [PASS] Test 4: Hand moving toward ultrasonic sensor fires alert: '{alerts[0][1]}'")
    passed += 1

    # Test 5: Immediate Contact Bumper (<= 25cm)
    total += 1
    stream = [
        (0.0, 18.0, []),
    ]
    alerts = simulate_pipeline(stream, is_walking=False, obstacle_moving=False)
    assert len(alerts) == 1 and "18 centimeters" in alerts[0][1], f"Test 5 Failed: Bumper alert failed, got {alerts}"
    print(f" [PASS] Test 5: Immediate bumper contact at 18cm fires emergency alert: '{alerts[0][1]}'")
    passed += 1

    # Test 6: Microphone Recording Mute (user_speaking=True)
    total += 1
    stream = [
        (0.0, 70.0, [{'name': 'chair', 'distance': 2.20}]),
        (0.2, 55.0, [{'name': 'chair', 'distance': 1.80}]),
        (0.4, 40.0, [{'name': 'chair', 'distance': 1.30}]),
    ]
    alerts = simulate_pipeline(stream, is_walking=True, obstacle_moving=True, user_speaking=True)
    assert len(alerts) == 0, f"Test 6 Failed: Alerts must be muted while speaking, got {alerts}"
    print(" [PASS] Test 6: Microphone recording active on phone completely mutes all hazard chimes!")
    passed += 1

    # Test 7: Cooldown limits alert rate (no rapid repeating spam)
    total += 1
    stream = [
        (0.0, 70.0, []),
        (0.2, 55.0, []),
        (0.4, 40.0, []), # Fires alert here at t=0.4
        (0.6, 30.0, []), # Only 0.2s elapsed -> blocked by cooldown
        (0.8, 26.0, []), # Only 0.4s elapsed -> blocked by cooldown
    ]
    alerts = simulate_pipeline(stream, is_walking=False, obstacle_moving=True)
    assert len(alerts) == 1, f"Test 7 Failed: Expected exactly 1 alert due to cooldown, got {len(alerts)}"
    print(" [PASS] Test 7: Cooldown prevents spamming within 2.0s window!")
    passed += 1

    print("=" * 70)
    print(f" ALL {passed}/{total} RATE-OF-CLOSURE VERIFICATION TESTS PASSED! ")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
