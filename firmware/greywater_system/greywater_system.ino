/*
 * ===========================================================================
 *  Automated IoT Greywater Recycling System
 *  Board: ESP32-WROOM-32 (Arduino IDE)
 * ===========================================================================
 *  5-tank pipeline:
 *    Tank 1 (Collection + gas screen) -> Tank 2 (passive filter, no code)
 *      -> Tank 3 (gas/turbidity/pH/temp analysis)
 *        -> Tank 4 (irrigation output, float-switch release)
 *        -> Tank 5 (toilet-flush output, float-switch release)
 *
 *  Features:
 *    - Reads all sensors on a fixed interval
 *    - Drives 6 solenoid valves via an 8-channel relay module
 *    - Publishes telemetry to Firebase Realtime Database
 *    - Accepts a remote manual-override "emergency drain" command
 *      pushed from the companion MIT App Inventor app
 *    - Fails safe: all valves default OFF on boot / WiFi loss
 *
 *  Required libraries (Arduino Library Manager):
 *    - Firebase ESP32 Client (by Mobizt)
 *    - OneWire
 *    - DallasTemperature
 *
 *  Author: <your name>
 *  License: MIT
 * ===========================================================================
 */

#include <WiFi.h>
#include <FirebaseESP32.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#include "config.h"

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------
FirebaseData   fbdo;
FirebaseAuth   auth;
FirebaseConfig fbConfig;

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

unsigned long lastSampleTime = 0;
bool manualOverride = false;

struct SensorReadings {
  int   tank1Gas;
  int   tank3Gas;
  int   tank3Turbidity;
  float tank3pH;
  float tank3TempC;
  bool  tank4Full;
  bool  tank5Full;
};

// ---------------------------------------------------------------------------
// Function prototypes
// (declared explicitly rather than relying on the Arduino IDE's automatic
//  prototype generation, which some toolchains — e.g. arduino-cli with a
//  stock ctags binary instead of Arduino's patched fork — do not perform)
// ---------------------------------------------------------------------------
void configureRelayPins();
void configureSensorPins();
void allValvesOff();
void connectWiFi();
void connectFirebase();
SensorReadings readAllSensors();
void printTelemetry(const SensorReadings &r);
void checkManualOverride();
void applyManualOverride();
void runAutomationLogic(const SensorReadings &r);
void pushTelemetryToFirebase(const SensorReadings &r);

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);

  configureRelayPins();
  configureSensorPins();
  allValvesOff(); // fail-safe default state

  tempSensor.begin();

  connectWiFi();
  connectFirebase();

  Serial.println(F("\n[SYSTEM] 5-Tank Greywater Recycling System Initialized."));
}

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------
void loop() {
  if (millis() - lastSampleTime >= SENSOR_INTERVAL_MS) {
    lastSampleTime = millis();

    SensorReadings r = readAllSensors();
    printTelemetry(r);

    checkManualOverride();

    if (manualOverride) {
      applyManualOverride();
    } else {
      runAutomationLogic(r);
    }

    pushTelemetryToFirebase(r);
  }
}

// ---------------------------------------------------------------------------
// Pin configuration
// ---------------------------------------------------------------------------
void configureRelayPins() {
  pinMode(SOL_1A_DRAIN, OUTPUT);
  pinMode(SOL_1B_FILTER, OUTPUT);
  pinMode(SOL_3A_IRRIGATION, OUTPUT);
  pinMode(SOL_3B_TOILET, OUTPUT);
  pinMode(SOL_TANK4_RELEASE, OUTPUT);
  pinMode(SOL_TANK5_RELEASE, OUTPUT);
}

void configureSensorPins() {
  pinMode(TANK1_GAS_PIN, INPUT);
  pinMode(TANK3_GAS_PIN, INPUT);
  pinMode(TANK3_TURBIDITY_PIN, INPUT);
  pinMode(TANK3_PH_PIN, INPUT);

  pinMode(TANK4_FLOAT_PIN, INPUT_PULLUP);
  pinMode(TANK5_FLOAT_PIN, INPUT_PULLUP);
}

void allValvesOff() {
  digitalWrite(SOL_1A_DRAIN, RELAY_OFF);
  digitalWrite(SOL_1B_FILTER, RELAY_OFF);
  digitalWrite(SOL_3A_IRRIGATION, RELAY_OFF);
  digitalWrite(SOL_3B_TOILET, RELAY_OFF);
  digitalWrite(SOL_TANK4_RELEASE, RELAY_OFF);
  digitalWrite(SOL_TANK5_RELEASE, RELAY_OFF);
}

// ---------------------------------------------------------------------------
// Connectivity
// ---------------------------------------------------------------------------
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print(F("[WIFI] Connecting"));
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.print(F("\n[WIFI] Connected. IP: "));
  Serial.println(WiFi.localIP());
}

void connectFirebase() {
  fbConfig.host = FIREBASE_HOST;
  fbConfig.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&fbConfig, &auth);
  Firebase.reconnectWiFi(true);
  Serial.println(F("[FIREBASE] Initialized."));
}

// ---------------------------------------------------------------------------
// Sensing
// ---------------------------------------------------------------------------
SensorReadings readAllSensors() {
  SensorReadings r;

  r.tank1Gas       = analogRead(TANK1_GAS_PIN);
  r.tank3Gas       = analogRead(TANK3_GAS_PIN);
  r.tank3Turbidity = analogRead(TANK3_TURBIDITY_PIN);

  int rawPh = analogRead(TANK3_PH_PIN);
  float voltage = (rawPh / 4095.0f) * 3.3f;
  r.tank3pH = 3.5f * voltage; // linear approximation - calibrate with pH 4/7/10 buffer solutions

  tempSensor.requestTemperatures();
  r.tank3TempC = tempSensor.getTempCByIndex(0);

  r.tank4Full = (digitalRead(TANK4_FLOAT_PIN) == LOW);
  r.tank5Full = (digitalRead(TANK5_FLOAT_PIN) == LOW);

  return r;
}

void printTelemetry(const SensorReadings &r) {
  Serial.println(F("---------------------------------------------"));
  Serial.printf("Tank1 Gas: %d\n", r.tank1Gas);
  Serial.printf("Tank3 Gas: %d | Turbidity: %d | pH: %.2f | Temp: %.1fC\n",
                r.tank3Gas, r.tank3Turbidity, r.tank3pH, r.tank3TempC);
  Serial.printf("Tank4 Full: %s | Tank5 Full: %s\n",
                r.tank4Full ? "YES" : "NO", r.tank5Full ? "YES" : "NO");
}

// ---------------------------------------------------------------------------
// Remote control
// ---------------------------------------------------------------------------
void checkManualOverride() {
  if (Firebase.getBool(fbdo, "/GreywaterSystem/Control/ManualDrain")) {
    manualOverride = fbdo.boolData();
  }
}

void applyManualOverride() {
  digitalWrite(SOL_TANK4_RELEASE, RELAY_ON);
  digitalWrite(SOL_TANK5_RELEASE, RELAY_ON);
  Serial.println(F("[OVERRIDE] Manual drain active — releasing Tank 4 & 5."));
}

// ---------------------------------------------------------------------------
// Automation logic
// ---------------------------------------------------------------------------
void runAutomationLogic(const SensorReadings &r) {
  // Stage 1: Tank 1 gas safety screening
  if (r.tank1Gas > TANK1_GAS_LIMIT) {
    digitalWrite(SOL_1A_DRAIN, RELAY_ON);
    digitalWrite(SOL_1B_FILTER, RELAY_OFF);
    Serial.println(F("[T1] Gas detected -> diverting to drainage."));
  } else {
    digitalWrite(SOL_1A_DRAIN, RELAY_OFF);
    digitalWrite(SOL_1B_FILTER, RELAY_ON);
    Serial.println(F("[T1] Safe -> moving to filtration tank."));
  }

  // Stage 2: Tank 3 water-quality evaluation
  bool gasOk       = (r.tank3Gas <= TANK3_GAS_LIMIT);
  bool turbidityOk = (r.tank3Turbidity >= TURBIDITY_LIMIT);
  bool phOk        = (r.tank3pH >= PH_MIN && r.tank3pH <= PH_MAX);
  bool tempOk      = (r.tank3TempC >= TEMP_MIN && r.tank3TempC <= TEMP_MAX);
  bool qualityOk   = gasOk && turbidityOk && phOk && tempOk;

  if (qualityOk) {
    digitalWrite(SOL_3A_IRRIGATION, RELAY_ON);
    digitalWrite(SOL_3B_TOILET, RELAY_OFF);
    Serial.println(F("[T3] Quality PASS -> routing to irrigation tank."));
  } else {
    digitalWrite(SOL_3A_IRRIGATION, RELAY_OFF);
    digitalWrite(SOL_3B_TOILET, RELAY_ON);
    Serial.println(F("[T3] Quality FAIL -> routing to toilet-flush tank."));
  }

  // Stage 3: Overflow release
  digitalWrite(SOL_TANK4_RELEASE, r.tank4Full ? RELAY_ON : RELAY_OFF);
  digitalWrite(SOL_TANK5_RELEASE, r.tank5Full ? RELAY_ON : RELAY_OFF);
  if (r.tank4Full) Serial.println(F("[T4] Full -> releasing to garden."));
  if (r.tank5Full) Serial.println(F("[T5] Full -> releasing to drainage."));
}

// ---------------------------------------------------------------------------
// Cloud telemetry
// ---------------------------------------------------------------------------
void pushTelemetryToFirebase(const SensorReadings &r) {
  FirebaseJson json;
  json.set("Tank1/Gas", r.tank1Gas);
  json.set("Tank3/Gas", r.tank3Gas);
  json.set("Tank3/Turbidity", r.tank3Turbidity);
  json.set("Tank3/pH", r.tank3pH);
  json.set("Tank3/Temp", r.tank3TempC);
  json.set("Status/Tank4_Full", r.tank4Full);
  json.set("Status/Tank5_Full", r.tank5Full);
  json.set("Status/ManualOverride", manualOverride);

  if (!Firebase.setJSON(fbdo, "/GreywaterSystem", json)) {
    Serial.print(F("[FIREBASE] Push failed: "));
    Serial.println(fbdo.errorReason());
  }
}
