#!/usr/bin/env python3
"""
Generates the KiCad schematic for the greywater treatment monitoring
project: ESP32 + pH/temperature/turbidity/gas(x2)/level sensors + 16x2
I2C LCD + voltage regulator + 5x (resistor -> BC547 transistor -> relay
-> flyback diode -> DC motor) driver stages.

Same verified methodology as the recycling-unit project:
  - Real symbol geometry pulled from the installed KiCad 7 libraries.
  - Verified coordinate transforms (rotation 0 and 180 only).
  - Every signal net routed as a real wire (no global labels for
    signals); power (GND/+5V/+12V) uses standard power-flag symbols.
  - Crossing-free "staircase lane" routing: every destination Y is kept
    on the same side of its own source Y as every other net's, which is
    the actual (verified) safety condition -- not just "same order".
  - Validated afterward with kicad-cli netlist export + an automated
    geometric crossing checker.
"""

import uuid, copy
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.schitems import (SchematicSymbol, Connection, Junction, NoConnect)
from kiutils.items.common import Position, Property, Effects, Font

SYM_DIR = "/usr/share/kicad/symbols"
OUT = "/home/claude/report_kicad/greywater-monitor.kicad_sch"

def load_symbol(libfile, entry_name, lib_id):
    lib = SymbolLib().from_file(f"{SYM_DIR}/{libfile}")
    for s in lib.symbols:
        if s.entryName == entry_name:
            s.libId = lib_id
            return s
    raise RuntimeError(f"{entry_name} not found in {libfile}")

def new_uuid():
    return str(uuid.uuid4())

def pinmap(sym):
    d = {}
    for u in sym.units:
        for p in u.pins:
            d[p.number] = (p.position.X, p.position.Y)
    return d

# ---------------------------------------------------------------------------
SYM_ESP32  = load_symbol("RF_Module.kicad_sym", "ESP32-WROOM-32", "RF_Module:ESP32-WROOM-32")
SYM_CONN02 = load_symbol("Connector_Generic.kicad_sym", "Conn_01x02", "Connector_Generic:Conn_01x02")
SYM_CONN03 = load_symbol("Connector_Generic.kicad_sym", "Conn_01x03", "Connector_Generic:Conn_01x03")
SYM_CONN04 = load_symbol("Connector_Generic.kicad_sym", "Conn_01x04", "Connector_Generic:Conn_01x04")
SYM_R      = load_symbol("Device.kicad_sym", "R", "Device:R")
SYM_D      = load_symbol("Device.kicad_sym", "D", "Diode:D")
SYM_Q      = load_symbol("Device.kicad_sym", "Q_NPN_BCE", "Device:Q_NPN_BCE")
SYM_RELAY  = load_symbol("Relay.kicad_sym", "Relay_SPDT", "Relay:Relay_SPDT")
SYM_MOTOR  = load_symbol("Motor.kicad_sym", "Motor_DC", "Motor:Motor_DC")
SYM_GND = load_symbol("power.kicad_sym", "GND", "power:GND")
SYM_5V  = load_symbol("power.kicad_sym", "+5V", "power:+5V")
SYM_12V = load_symbol("power.kicad_sym", "+12V", "power:+12V")

PINS_ESP32  = pinmap(SYM_ESP32)
PINS_CONN02 = pinmap(SYM_CONN02)
PINS_CONN03 = pinmap(SYM_CONN03)
PINS_CONN04 = pinmap(SYM_CONN04)
PINS_R      = pinmap(SYM_R)
PINS_D      = pinmap(SYM_D)
PINS_Q      = pinmap(SYM_Q)
PINS_RELAY  = pinmap(SYM_RELAY)
PINS_MOTOR  = pinmap(SYM_MOTOR)

sch = Schematic.create_new()
sch.paper.paperSize = "A1"
sch.libSymbols = [SYM_ESP32, SYM_CONN02, SYM_CONN03, SYM_CONN04, SYM_R, SYM_D,
                   SYM_Q, SYM_RELAY, SYM_MOTOR, SYM_GND, SYM_5V, SYM_12V]

ref_counters = {}
def next_ref(prefix):
    ref_counters[prefix] = ref_counters.get(prefix, 0) + 1
    return f"{prefix}{ref_counters[prefix]}"

def place(lib_id, value, x, y, rotation=0, ref=None, prefix=None):
    if ref is None:
        ref = next_ref(prefix)
    s = SchematicSymbol()
    s.libId = lib_id
    s.position = Position(X=x, Y=y, angle=rotation)
    s.unit = 1
    s.inBom = True
    s.onBoard = True
    s.uuid = new_uuid()
    small = Effects(font=Font(height=1.27, width=1.27))
    s.properties = [
        Property(key="Reference", value=ref, position=Position(X=x+3, Y=y-3, angle=0), effects=small),
        Property(key="Value", value=value, position=Position(X=x+3, Y=y+3, angle=0), effects=small),
    ]
    sch.schematicSymbols.append(s)
    return {"ref": ref, "x": x, "y": y, "rot": rotation}

def pin_abs(inst, pins, number):
    lx, ly = pins[str(number)]
    if inst["rot"] == 0:
        return (round(inst["x"] + lx, 3), round(inst["y"] - ly, 3))
    elif inst["rot"] == 180:
        return (round(inst["x"] - lx, 3), round(inst["y"] + ly, 3))
    raise NotImplementedError

def wire(p1, p2):
    if p1 == p2:
        return
    sch.graphicalItems.append(Connection(type="wire",
        points=[Position(X=p1[0], Y=p1[1]), Position(X=p2[0], Y=p2[1])], uuid=new_uuid()))

def junction(pt):
    j = Junction()
    j.position = Position(X=pt[0], Y=pt[1], angle=0)
    j.uuid = new_uuid()
    sch.junctions.append(j)

def no_connect(pt):
    nc = NoConnect()
    nc.position = Position(X=pt[0], Y=pt[1], angle=0)
    nc.uuid = new_uuid()
    sch.noConnects.append(nc)

def power_stub(pin_pt, lib_id, dx, dy):
    end = (pin_pt[0] + dx, pin_pt[1] + dy)
    wire(pin_pt, end)
    place(lib_id, lib_id.split(":")[1], end[0], end[1], prefix="#PWR")

def staircase(src, dest, lane_x):
    if src[1] == dest[1]:
        wire(src, dest); return
    wire(src, (lane_x, src[1]))
    wire((lane_x, src[1]), (lane_x, dest[1]))
    wire((lane_x, dest[1]), dest)

# ---------------------------------------------------------------------------
# ESP32
# ---------------------------------------------------------------------------
ESP = place("RF_Module:ESP32-WROOM-32", "ESP32-WROOM-32", 300, 400, ref="U1")
power_stub(pin_abs(ESP, PINS_ESP32, 2), "power:+5V", 0, -8)
for i, pin in enumerate(["1", "15", "38", "39"]):
    power_stub(pin_abs(ESP, PINS_ESP32, pin), "power:GND", -6 - i*4, 8)

# ---------------------------------------------------------------------------
# Merged, order-preserving destination list (see header docstring for the
# safety argument). Values are hand-verified safe destinations satisfying
# dest_i < source_i for every net while staying monotonically increasing.
# ---------------------------------------------------------------------------
COL_C_X = 380
LANE_X0 = 320
LANE_DX = 1.5

rows = [
    ("16", "SCL",       104.94, "lcd"),
    ("23", "RELAY_1",   122.94, "relay"),
    ("27", "RELAY_2",   162.94, "relay"),
    ("28", "RELAY_3",   202.94, "relay"),
    ("30", "RELAY_4",   242.94, "relay"),
    ("31", "RELAY_5",   282.94, "relay"),
    ("10", "GAS1",      322.94, "conn3"),
    ("11", "GAS2",      340.94, "conn3"),
    ("12", "LEVEL",     358.94, "conn3"),
    ("8",  "TURB_AO",   376.94, "conn4"),
    ("6",  "TEMP_AO",   394.94, "conn3"),
    ("7",  "PH_PO",     412.94, "conn3"),
]
lanes = {net: LANE_X0 + i * LANE_DX for i, (_, net, _, _) in enumerate(rows)}

# --- LCD (Conn_01x04: SCL, SDA, VCC, GND) ---
_, net, row_y, _ = rows[0]
LCD = place("Connector_Generic:Conn_01x04", "LCD_16x2_I2C", COL_C_X, row_y, prefix="J")
scl_pt = pin_abs(LCD, PINS_CONN04, 1)
staircase(pin_abs(ESP, PINS_ESP32, rows[0][0]), scl_pt, lanes["SCL"])
sda_pt = pin_abs(LCD, PINS_CONN04, 2)
staircase(pin_abs(ESP, PINS_ESP32, "13"), sda_pt, lanes["SCL"] + 0.6)
power_stub(pin_abs(LCD, PINS_CONN04, 3), "power:+5V", -8, 0)
power_stub(pin_abs(LCD, PINS_CONN04, 4), "power:GND", -8, 0)

# --- 5x Relay/transistor/motor driver stages ---
for pin, net, row_y, _ in rows[1:6]:
    r_sym_x = COL_C_X - 40
    R = place("Device:R", "10k", r_sym_x, row_y + 3.81, prefix="R")
    r_top = pin_abs(R, PINS_R, 1)
    r_bot = pin_abs(R, PINS_R, 2)
    staircase(pin_abs(ESP, PINS_ESP32, pin), r_top, lanes[net])

    q_sym_x = COL_C_X + 10
    Q = place("Device:Q_NPN_BCE", "BC547", q_sym_x, row_y, prefix="Q")
    b_pt = pin_abs(Q, PINS_Q, "1")
    jog_x = r_bot[0] + 6
    wire(r_bot, (jog_x, r_bot[1]))
    wire((jog_x, r_bot[1]), (jog_x, row_y))
    wire((jog_x, row_y), b_pt)

    e_pt = pin_abs(Q, PINS_Q, "3")
    power_stub(e_pt, "power:GND", 0, 8)

    c_pt = pin_abs(Q, PINS_Q, "2")
    rly_sym_x = q_sym_x + 40
    RLY = place("Relay:Relay_SPDT", "Relay_module", rly_sym_x, row_y + 7.62, prefix="K")
    a1 = pin_abs(RLY, PINS_RELAY, "A1")
    wire(c_pt, (c_pt[0], a1[1]))
    wire((c_pt[0], a1[1]), a1)

    power_stub(pin_abs(RLY, PINS_RELAY, "A2"), "power:GND", 12, 0)
    power_stub(pin_abs(RLY, PINS_RELAY, "11"), "power:+12V", 24, 0)
    no_connect(pin_abs(RLY, PINS_RELAY, "12"))

    no_pt = pin_abs(RLY, PINS_RELAY, "14")
    assert abs(no_pt[1] - row_y) < 0.01

    m_sym_x = no_pt[0] + 35
    M = place("Motor:Motor_DC", f"Motor_{net}", m_sym_x, row_y - 5.08, prefix="M")
    m_plus = pin_abs(M, PINS_MOTOR, 1)
    wire(no_pt, m_plus)
    power_stub(pin_abs(M, PINS_MOTOR, 2), "power:GND", 10, 0)

    d_sym_x = no_pt[0] + 15
    D = place("Diode:D", "1N4007", d_sym_x, row_y, prefix="D")
    junction(no_pt)
    wire(no_pt, pin_abs(D, PINS_D, 2))
    power_stub(pin_abs(D, PINS_D, 1), "power:+12V", 6, 0)

# --- Simple 3-pin sensors (GAS1, GAS2, LEVEL, TEMP, PH): 1=VCC,2=SIG,3=GND ---
for pin, net, row_y, kind in rows[6:]:
    if kind != "conn3":
        continue
    label = {"GAS1":"Gas_sensor_1","GAS2":"Gas_sensor_2","LEVEL":"Level_sensor",
              "TEMP_AO":"Temperature_sensor","PH_PO":"pH_sensor"}[net]
    C = place("Connector_Generic:Conn_01x03", label, COL_C_X, row_y, prefix="J")
    sig_pt = pin_abs(C, PINS_CONN03, 2)
    staircase(pin_abs(ESP, PINS_ESP32, pin), sig_pt, lanes[net])
    power_stub(pin_abs(C, PINS_CONN03, 1), "power:+5V", -8, 0)
    power_stub(pin_abs(C, PINS_CONN03, 3), "power:GND", -8, 0)

# --- Turbidity sensor (Conn_01x04: VCC, AO, DO, GND) ---
_, net, row_y, _ = rows[9]
TURB = place("Connector_Generic:Conn_01x04", "Turbidity_sensor", COL_C_X, row_y, prefix="J")
ao_pt = pin_abs(TURB, PINS_CONN04, 2)
staircase(pin_abs(ESP, PINS_ESP32, "8"), ao_pt, lanes["TURB_AO"])
do_pt = pin_abs(TURB, PINS_CONN04, 3)
staircase(pin_abs(ESP, PINS_ESP32, "9"), do_pt, lanes["TURB_AO"] + 0.6)
power_stub(pin_abs(TURB, PINS_CONN04, 1), "power:+5V", -8, 0)
power_stub(pin_abs(TURB, PINS_CONN04, 4), "power:GND", -8, 0)

# ---------------------------------------------------------------------------
# Power section: 12V + 5V inputs -> regulator -> ESP32 VIN / +5V rail
# ---------------------------------------------------------------------------
J_PWR = place("Connector_Generic:Conn_01x02", "12V_DC_IN", 40, 60, prefix="J")
power_stub(pin_abs(J_PWR, PINS_CONN02, 1), "power:+12V", -8, 0)
power_stub(pin_abs(J_PWR, PINS_CONN02, 2), "power:GND", -8, 0)

ref_counters["U"] = 1  # U1 = ESP32, assigned manually above
REG = place("Connector_Generic:Conn_01x04", "Voltage_regulator_12to5V", 40, 100, prefix="U")
power_stub(pin_abs(REG, PINS_CONN04, 1), "power:+12V", -8, 0)  # IN
power_stub(pin_abs(REG, PINS_CONN04, 2), "power:GND", -8, 0)   # GND
power_stub(pin_abs(REG, PINS_CONN04, 3), "power:+5V", -8, 0)   # OUT (also feeds ESP32 VIN)
power_stub(pin_abs(REG, PINS_CONN04, 4), "power:GND", -8, 0)   # EN tied low/GND-referenced

# ---------------------------------------------------------------------------
sch.to_file(OUT)
print("Schematic written:", OUT)
print("Symbols:", len(sch.schematicSymbols), " Wires:", len(sch.graphicalItems),
      " Junctions:", len(sch.junctions), " NoConnects:", len(sch.noConnects))
