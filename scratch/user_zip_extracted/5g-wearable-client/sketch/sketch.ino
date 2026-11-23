// =========================================================================
// 5G WEARABLE ASSISTIVE DEVICE - STREAMLINED ULTRASONIC MCU FIRMWARE
// Designed for Visually Impaired Navigation
// Target: Arduino UNO Q (Zephyr MCU Core)
// Hardware: HC-SR04 Ultrasonic Distance Sensor on Pins 12 & 13
// Output: Serial JSON Telemetry at 10 Hz + Arduino RouterBridge RPC to Python
// =========================================================================

#include <Arduino_RouterBridge.h>

// --- PIN DEFINITIONS ---
#define PIN_TRIG            12  // HC-SR04 Ultrasonic Trigger
#define PIN_ECHO            13  // HC-SR04 Ultrasonic Echo

// --- LIVE HARDWARE / TEST MODE ---
// Set to false for actual live hardware with physical HC-SR04 wired.
// Set to true if running synthetic testing before wiring sensors.
#define SIMULATION_TEST_MODE  false

// --- TIMING CONSTANTS (Non-blocking with millis) ---
const unsigned long SENSOR_INTERVAL_MS    = 60;   // 16 Hz ultrasonic scan rate
const unsigned long TELEMETRY_INTERVAL_MS = 100;  // 10 Hz telemetry uplink

unsigned long lastSensorReadTime = 0;
unsigned long lastTelemetryTime  = 0;

// Current filtered distance (centimeters)
float currentDistanceCm = 400.0f;

// -------------------------------------------------------------------------
// Fast, Noise-Resistant Ultrasonic Distance Read
// -------------------------------------------------------------------------
float readUltrasonicDistanceCM() {
#if SIMULATION_TEST_MODE
    // Smooth synthetic proximity wave: 190cm -> 20cm -> 190cm
    static float simDist = 190.0f;
    static float simStep = -3.5f;
    simDist += simStep;
    if (simDist <= 20.0f) {
        simDist = 20.0f;
        simStep = 4.0f;
    } else if (simDist >= 220.0f) {
        simDist = 220.0f;
        simStep = -3.5f;
    }
    return simDist;
#else
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);

    // Timeout of 12000 microseconds limits search range to ~2.0m, preventing blocking delays
    long duration = pulseIn(PIN_ECHO, HIGH, 12000);
    if (duration <= 0) {
        return 400.0f; // Clear pathway / no obstacle within 2 meters
    }
    
    float distance = (duration * 0.0343f) / 2.0f;
    if (distance <= 2.0f) {
        return 400.0f; // Reject sensor noise / physical dead-zone glitches
    }
    return distance;
#endif
}

// -------------------------------------------------------------------------
// RouterBridge RPC Callback for Python
// -------------------------------------------------------------------------
float get_distance() {
    return currentDistanceCm;
}

// -------------------------------------------------------------------------
// Broadcast telemetry packet over Serial to USB / Serial Monitor
// -------------------------------------------------------------------------
void sendTelemetryPacket(float dist_cm) {
    char buffer[48];
    snprintf(buffer, sizeof(buffer), "{\"dist\":%.1f}", dist_cm);
    Serial.println(buffer);
}

// -------------------------------------------------------------------------
// Setup
// -------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);

    // Initialize Bridge for inter-core communication with Python
    Bridge.begin();
    Bridge.provide("get_distance", get_distance);

    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_ECHO, INPUT);

    digitalWrite(PIN_TRIG, LOW);

    Serial.println("🟢 [MCU READY]: Arduino UNO Q Ultrasonic & RouterBridge Online");
}

// -------------------------------------------------------------------------
// Main Loop (100% Non-Blocking)
// -------------------------------------------------------------------------
void loop() {
    unsigned long now = millis();

    // 1. Ultrasonic Proximity Scan (16 Hz)
    if (now - lastSensorReadTime >= SENSOR_INTERVAL_MS) {
        lastSensorReadTime = now;
        float rawDist = readUltrasonicDistanceCM();
        
        // Exponential moving average filter for noise suppression
        if (rawDist > 0.0f && rawDist < 400.0f) {
            currentDistanceCm = (0.65f * currentDistanceCm) + (0.35f * rawDist);
        } else {
            currentDistanceCm = (0.80f * currentDistanceCm) + (0.20f * 400.0f);
        }
    }

    // 2. Periodic Telemetry Stream (10 Hz)
    if (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryTime = now;
        sendTelemetryPacket(currentDistanceCm);
    }
}
