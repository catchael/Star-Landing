"""UNO Q WebUI backend: mission rules, energy, scoring and hull state."""
from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
import time

ui = WebUI()
received_count = 0
boost_presses = 0
fire_presses = 0
controller_sessions = {}
event_ids = set()
last_input_at = time.monotonic()
last_update_at = last_input_at
control_x = 0.0
control_y = 0.0
boost_until = 0.0
energy = 100.0
distance = 0.0
mission_status = "flying"
hull = 3
score = 0
calibration = {
    "phase": "flight", "stage": 0, "total": 0, "title": "", "hint": "",
    "countdown": 0, "recording": False, "progress": 0.0,
    "left_seen": False, "right_seen": False, "camera_url": "",
}
preflight_active = False


def advance_simulation(now):
    global last_update_at, energy, distance, mission_status
    dt = max(0.0, min(0.25, now - last_update_at))
    last_update_at = now
    connected = now - last_input_at < 2.5

    if mission_status == "flying" and connected:
        sprinting = now < boost_until
        energy = max(0.0, energy - 0.12 * dt)
        distance = min(30.0, distance + (0.36 + (0.70 if sprinting else 0.0)) * dt)
        if hull <= 0:
            mission_status = "destroyed"
        elif energy <= 0:
            mission_status = "energy_empty"
        elif distance >= 30.0:
            mission_status = "landed" if energy >= 20.0 else "energy_low"


def receive_input(data: dict):
    global received_count, boost_presses, fire_presses, last_input_at
    global control_x, control_y, boost_until, energy
    try:
        client_id = str(data.get("client_id", "default"))[:100]
        seq = int(data.get("seq", 0))
        x = max(-1.0, min(1.0, float(data.get("x", 0))))
        y = max(-1.0, min(1.0, float(data.get("y", 0))))
        boost_events = max(0, int(data.get("boost_events", 0)))
        fire_events = max(0, int(data.get("fire_events", 0)))
    except (AttributeError, TypeError, ValueError):
        return {"ok": False, "error": "invalid control data"}

    session = controller_sessions.setdefault(client_id, {"seq": 0, "boost_events": 0, "fire_events": 0})
    if seq <= session["seq"]:
        return {"ok": True, "seq": seq, "received": received_count,
                "boost_presses": boost_presses, "fire_presses": fire_presses}

    now = time.monotonic()
    advance_simulation(now)
    session["seq"] = seq
    received_count += 1
    last_input_at = now
    control_x, control_y = x, y

    new_boosts = max(0, boost_events - session["boost_events"])
    new_shots = max(0, fire_events - session["fire_events"])
    session["boost_events"] = max(session["boost_events"], boost_events)
    session["fire_events"] = max(session["fire_events"], fire_events)
    if len(controller_sessions) > 32:
        oldest = next(iter(controller_sessions))
        if oldest != client_id:
            controller_sessions.pop(oldest, None)
    if mission_status == "flying":
        for _ in range(new_boosts):
            boost_presses += 1
            boost_until = max(boost_until, now) + 1.2
            energy = max(0.0, energy - 8.0)
            print(f"BUTTON boost #{boost_presses} (seq {seq})", flush=True)
        for _ in range(new_shots):
            fire_presses += 1
            energy = max(0.0, energy - 3.0)
            print(f"BUTTON fire #{fire_presses} (seq {seq})", flush=True)

    return {"ok": True, "seq": seq, "received": received_count,
            "boost_presses": boost_presses, "fire_presses": fire_presses}


def update_preflight(data: dict):
    global calibration, preflight_active, mission_status, energy, distance
    global hull, score, boost_until, last_update_at, last_input_at, control_x, control_y
    global boost_presses, fire_presses
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid calibration data"}
    phase = str(data.get("phase", "align"))[:24]
    now = time.monotonic()
    if phase == "align" and not preflight_active:
        preflight_active = True
        mission_status = "preflight"
        energy, distance, hull, score, boost_until = 100.0, 0.0, 3, 0, 0.0
        boost_presses = fire_presses = 0
        control_x = control_y = 0.0
        last_update_at = last_input_at = now
        event_ids.clear()
    calibration = {
        "phase": phase,
        "stage": max(0, min(9, int(data.get("stage", 0)))),
        "total": max(0, min(9, int(data.get("total", 0)))),
        "title": str(data.get("title", ""))[:48],
        "hint": str(data.get("hint", ""))[:96],
        "countdown": max(0.0, min(10.0, float(data.get("countdown", 0)))),
        "recording": bool(data.get("recording", False)),
        "progress": max(0.0, min(1.0, float(data.get("progress", 0)))),
        "left_seen": bool(data.get("left_seen", False)),
        "right_seen": bool(data.get("right_seen", False)),
        "camera_url": str(data.get("camera_url", calibration.get("camera_url", "")))[:180],
    }
    if phase == "flight":
        preflight_active = False
        mission_status = "flying"
        last_update_at = last_input_at = now
        print("PREFLIGHT complete; flight started", flush=True)
    elif phase not in ("align", "countdown", "recording", "actions", "takeoff", "error"):
        return {"ok": False, "error": "unknown preflight phase"}
    last_input_at = now
    return {"ok": True, "phase": phase}


def report_event(data: dict):
    global hull, score, mission_status
    try:
        event_id = str(data.get("event_id", ""))
        event_type = str(data.get("type", ""))
    except AttributeError:
        return {"ok": False}
    if not event_id or event_id in event_ids:
        return {"ok": True, "hull": hull, "score": score}
    event_ids.add(event_id)
    if len(event_ids) > 500:
        event_ids.clear()
        event_ids.add(event_id)
    if mission_status != "flying":
        return {"ok": True, "hull": hull, "score": score}
    if event_type == "collision":
        hull = max(0, hull - 1)
        print(f"HULL impact: {hull}/3", flush=True)
    elif event_type == "meteor_destroyed":
        score += 100
        print(f"SCORE meteor destroyed: {score}", flush=True)
    return {"ok": True, "hull": hull, "score": score}


def get_state():
    now = time.monotonic()
    advance_simulation(now)
    return {
        "x": round(control_x, 3), "y": round(control_y, 3),
        "energy": round(energy, 1), "distance": round(distance, 1),
        "status": mission_status, "boost": now < boost_until,
        "boost_presses": boost_presses, "fire_presses": fire_presses,
        "hull": hull, "score": score,
        "connected": now - last_input_at < 2.5,
        "calibration": calibration,
    }


def reset_game():
    global energy, distance, mission_status, boost_until
    global last_update_at, last_input_at, hull, score, preflight_active, calibration
    energy, distance, mission_status = 100.0, 0.0, "flying"
    boost_until = 0.0
    hull, score = 3, 0
    last_update_at = last_input_at = time.monotonic()
    preflight_active = False
    calibration = {"phase": "flight", "stage": 0, "total": 0, "title": "", "hint": "",
                   "countdown": 0, "recording": False, "progress": 0,
                   "left_seen": False, "right_seen": False, "camera_url": ""}
    print("MISSION reset", flush=True)
    return {"ok": True}


ui.expose_api("POST", "/input", receive_input)
ui.expose_api("POST", "/preflight", update_preflight)
ui.expose_api("POST", "/event", report_event)
ui.expose_api("GET", "/state", get_state)
ui.expose_api("POST", "/reset", reset_game)
print("Star Landing WebUI starting on port 7000", flush=True)
App.run()
