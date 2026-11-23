"""
Automated Verification Suite: Threat Detection & Ultrasonic Proximity Gating
Tests all critical safety scenarios for the 5G Assistive Wearable:
1. Stationary Chair detection at 1.1m (Critical Zone) -> Must Alert!
2. Stationary Person detection at 1.1m (Critical Zone) -> Must Alert!
3. Stationary Chair at 2.5m (Warning Zone) -> Suppressed (no desk spam)
4. Moving Chair or Walking user at 2.5m (Warning Zone) -> Must Alert!
5. Ultrasonic Hand Proximity at 19.5cm -> Must Alert Critical Stop!
6. Ultrasonic Touching Proximity at 12.0cm -> Must Alert Touching Stop!
7. Ultrasonic Caution Proximity at 75.0cm -> Must Alert Caution!
8. Sensor Fusion: Ultrasonic 45cm + Vision Chair -> "Stop! chair 45 centimeters"!
9. Cooldown verification for critical vs warning alerts.
"""

import sys
import time

def evaluate_threat_and_ultrasonic(
    valid_threats,
    current_ultra,
    is_walking,
    obstacle_moving,
    now,
    last_alert_time,
    nav_speaking=False,
    critical_dist_m=1.5,
    alert_dist_m=3.5,
    cooldown_crit=0.8,
    cooldown_warn=1.8
):
    """
    Mirror of the exact dual-layer hazard detection algorithm in edge_server/server.py.
    Returns (alert_triggered, warning_msg, urgency_level, new_last_alert_time, source).
    """
    alert_dispatched = False
    warning_msg = None
    urgency_level = None
    source = None

    # LAYER 1: Wearable Ultrasonic Proximity Alarm
    if current_ultra is not None and 2.0 <= current_ultra <= 100.0:
        is_ultra_critical = (current_ultra <= 50.0)
        ultra_cooldown = cooldown_crit if is_ultra_critical else cooldown_warn
        
        if (now - last_alert_time) > ultra_cooldown and not nav_speaking:
            fused_name = "obstacle"
            if valid_threats and valid_threats[0]['distance'] <= 2.2:
                fused_name = valid_threats[0]['name']
                
            urgency_level = "critical" if is_ultra_critical else "warning"
            dist_m = round(current_ultra / 100.0, 2)
            
            if current_ultra <= 15.0:
                warning_msg = f"Stop! {fused_name} touching, {int(current_ultra)} centimeters"
            elif is_ultra_critical:
                warning_msg = f"Stop! {fused_name} {int(current_ultra)} centimeters"
            else:
                warning_msg = f"Caution! {fused_name} {int(current_ultra)} centimeters"
                
            last_alert_time = now
            alert_dispatched = True
            source = "ultrasonic"

    # LAYER 2: Vision AI Threat Evaluation
    if not alert_dispatched and valid_threats:
        primary = valid_threats[0]
        dist = primary['distance']
        p_name = primary['name']
        
        if dist <= alert_dist_m:
            is_critical = (dist <= critical_dist_m)
            ultra_confirms = (current_ultra is not None and current_ultra <= 250.0)
            should_alert = is_critical or is_walking or obstacle_moving or ultra_confirms
            
            active_cooldown = cooldown_crit if is_critical else cooldown_warn
            cooldown_ready = (now - last_alert_time) > active_cooldown
            
            if should_alert and not nav_speaking and cooldown_ready:
                urgency_level = "critical" if is_critical else "warning"
                if is_critical:
                    warning_msg = f"Stop! {p_name} {float(dist):.1f} meters"
                else:
                    warning_msg = f"{p_name} ahead, {float(dist):.1f} meters"
                    
                last_alert_time = now
                alert_dispatched = True
                source = "vision"

    return alert_dispatched, warning_msg, urgency_level, last_alert_time, source


def run_all_tests():
    passed = 0
    total = 0

    print("=" * 70)
    print("RUNNING PIPELINE VERIFICATION SUITE: THREAT DETECTION & ULTRASONIC")
    print("=" * 70)

    # Test 1: Stationary Chair at 1.1m (User sitting at desk)
    total += 1
    threats = [{'name': 'chair', 'distance': 1.1}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "critical" and "chair" in msg and "1.1" in msg, f"Test 1 Failed: {msg}"
    print(" [PASS] Test 1: Stationary Chair at 1.1m triggers CRITICAL Stop alert on phone!")
    passed += 1

    # Test 2: Stationary Person at 1.1m
    total += 1
    threats = [{'name': 'person', 'distance': 1.1}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "critical" and "person" in msg, f"Test 2 Failed: {msg}"
    print(" [PASS] Test 2: Stationary Person at 1.1m triggers CRITICAL Stop alert!")
    passed += 1

    # Test 3: Stationary Chair at 2.5m (Desk background object - should be quiet)
    total += 1
    threats = [{'name': 'chair', 'distance': 2.5}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert not triggered, f"Test 3 Failed: expected no alert, got {msg}"
    print(" [PASS] Test 3: Distant stationary Chair at 2.5m is properly silenced when seated!")
    passed += 1

    # Test 4: Moving Chair or User Walking towards Chair at 2.5m
    total += 1
    threats = [{'name': 'chair', 'distance': 2.5}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=True,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "warning" and "chair ahead, 2.5 meters" in msg, f"Test 4 Failed: {msg}"
    print(" [PASS] Test 4: Walking user approaching chair at 2.5m triggers CAUTION warning!")
    passed += 1

    # Test 5: Hand in front of HC-SR04 at 19.5cm (From Arduino Screenshot)
    total += 1
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=[],
        current_ultra=19.5,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "critical" and src == "ultrasonic" and "19 centimeters" in msg, f"Test 5 Failed: {msg}"
    print(" [PASS] Test 5: Hand at 19.5cm triggers ULTRASONIC Critical Stop alert ('Stop! obstacle 19 centimeters')!")
    passed += 1

    # Test 6: Touching obstacle at 12cm
    total += 1
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=[],
        current_ultra=12.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "critical" and "touching, 12 centimeters" in msg, f"Test 6 Failed: {msg}"
    print(" [PASS] Test 6: Touching obstacle at 12cm triggers 'Stop! obstacle touching, 12 centimeters'!")
    passed += 1

    # Test 7: Caution obstacle at 75cm
    total += 1
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=[],
        current_ultra=75.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and urg == "warning" and "Caution! obstacle 75 centimeters" in msg, f"Test 7 Failed: {msg}"
    print(" [PASS] Test 7: Obstacle at 75cm triggers 'Caution! obstacle 75 centimeters'!")
    passed += 1

    # Test 8: Sensor Fusion (Chair visible + Ultrasonic at 45cm)
    total += 1
    threats = [{'name': 'chair', 'distance': 1.2}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=45.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0
    )
    assert triggered and "chair 45 centimeters" in msg, f"Test 8 Failed: {msg}"
    print(" [PASS] Test 8: Sensor Fusion fuses Vision + Ultrasonic -> 'Stop! chair 45 centimeters'!")
    passed += 1

    # Test 9: Cooldown gating blocks spamming within 0.8s
    total += 1
    threats = [{'name': 'chair', 'distance': 1.1}]
    triggered, msg, urg, t_alert, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=9.5  # Only 0.5s elapsed, cooldown is 0.8s
    )
    assert not triggered, f"Test 9 Failed: cooldown was violated"
    print(" [PASS] Test 9: Cooldown correctly prevents rapid repeated alert chatter within 0.8s!")
    passed += 1

    # Test 10: Navigation preemption blocks hazard while speaking directions
    total += 1
    threats = [{'name': 'chair', 'distance': 1.1}]
    triggered, msg, urg, _, src = evaluate_threat_and_ultrasonic(
        valid_threats=threats,
        current_ultra=400.0,
        is_walking=False,
        obstacle_moving=False,
        now=10.0,
        last_alert_time=0.0,
        nav_speaking=True  # Navigation actively giving turn instruction
    )
    assert not triggered, f"Test 10 Failed: nav_speaking was not respected"
    print(" [PASS] Test 10: Turn navigation voice preemption prevents overlapping audio collision!")
    passed += 1

    print("=" * 70)
    print(f" ALL {passed}/{total} VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
