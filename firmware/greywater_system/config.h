/*
 * config.h
 * ---------------------------------------------------------
 * Edit this file with YOUR credentials and calibration values.
 * Keeping this separate from the main .ino means you can add
 * config.h to .gitignore if you don't want to publish your
 * WiFi/Firebase secrets on GitHub (recommended).
 * ---------------------------------------------------------
 */

#ifndef CONFIG_H
#define CONFIG_H

// ---------------- WIFI CREDENTIALS ----------------
#define WIFI_SSID       "YOUR_WIFI_SSID"
#define WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"

// ---------------- FIREBASE CREDENTIALS ----------------
// Realtime Database URL, e.g. https://your-project-id-default-rtdb.firebaseio.com/
#define FIREBASE_HOST   "https://your-project-id-default-rtdb.firebaseio.com/"
// Project Settings -> Service Accounts -> Database Secrets (legacy token)
// or a Web API key, depending on your Firebase library auth method.
#define FIREBASE_AUTH   "YOUR_FIREBASE_DATABASE_SECRET_OR_API_KEY"

// ---------------- PIN DEFINITIONS ----------------
// Analog sensors (use ADC1 pins only: 32-39, so WiFi keeps working)
#define TANK1_GAS_PIN         34   // Tank 1 gas sensor (MQ-135/MQ-2)
#define TANK3_GAS_PIN         35   // Tank 3 gas sensor
#define TANK3_TURBIDITY_PIN   32   // Tank 3 turbidity sensor
#define TANK3_PH_PIN          33   // Tank 3 pH sensor

// Digital / OneWire
#define ONE_WIRE_BUS          4    // DS18B20 temperature sensor data pin
#define TANK4_FLOAT_PIN       18   // Irrigation tank float switch
#define TANK5_FLOAT_PIN       19   // Toilet-flush tank float switch

// Relay / solenoid outputs
#define SOL_1A_DRAIN          21   // Tank 1 -> Drainage   (harmful gas)
#define SOL_1B_FILTER         22   // Tank 1 -> Tank 2      (safe water)
#define SOL_3A_IRRIGATION     23   // Tank 3 -> Tank 4      (quality pass)
#define SOL_3B_TOILET         25   // Tank 3 -> Tank 5      (quality fail)
#define SOL_TANK4_RELEASE     26   // Tank 4 -> Garden      (full)
#define SOL_TANK5_RELEASE     27   // Tank 5 -> Drainage    (full)

// Relay module logic level. Most cheap modules are ACTIVE-LOW.
// If your relays turn ON when the pin is HIGH, swap these two.
#define RELAY_ON   LOW
#define RELAY_OFF  HIGH

// ---------------- CALIBRATED THRESHOLDS ----------------
// IMPORTANT: These are starting points only. Dip each sensor in clean
// water and in real greywater, log the raw ADC values via Serial Monitor,
// and adjust these thresholds to match YOUR specific sensors.
#define TANK1_GAS_LIMIT     1800   // Above this = unsafe gas level
#define TANK3_GAS_LIMIT     1800
#define TURBIDITY_LIMIT     2200   // Higher raw ADC = clearer water (sensor-dependent!)
#define PH_MIN              6.0f
#define PH_MAX              8.5f
#define TEMP_MIN            10.0f // deg C
#define TEMP_MAX            45.0f // deg C

// ---------------- TIMING ----------------
#define SENSOR_INTERVAL_MS  3000UL   // How often to read sensors / update Firebase

#endif // CONFIG_H
