from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# In-memory vehicle store: {vehicle_id: {lat, lon, mode, last_update}}
vehicle_data = {}

# In-memory tracking store: {vehicle_id: bool}
tracking_status = {}

# --- LOGIN CONFIG ---
VALID_USERNAME = "admin"
VALID_PASSWORD = "mypassword"

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "error": "Invalid username or password"}), 401


@app.route("/api/location/update", methods=["GET"])
def update_location():
    """Update location via GET params: id, lat, lon, mode"""
    vehicle_id = request.args.get("id")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    mode = request.args.get("mode")

    if not all([vehicle_id, lat, lon, mode]):
        return "Missing parameters", 400

    vehicle_data[vehicle_id] = {
        "lat": float(lat),
        "lon": float(lon),
        "mode": mode.strip().lower(),
        "last_update": time.time()
    }

    return f"Location updated for {vehicle_id}", 200


@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    vehicles = []

    for vehicle_id, info in vehicle_data.items():
        if not tracking_status.get(vehicle_id, False):
            continue

        lat, lon = info["lat"], info["lon"]
        age = now - info["last_update"]

        eta_min = round(5 + (age / 60))  # Placeholder ETA

        vehicles.append({
            "id": vehicle_id,
            "lat": lat,
            "lon": lon,
            "mode": info.get("mode", "unknown"),
            "eta_min": eta_min
        })

    return jsonify({"vehicles": vehicles})


@app.route("/api/vehicles/clear", methods=["POST"])
def clear_vehicles():
    vehicle_data.clear()
    return jsonify({"status": "cleared", "message": "All vehicles removed"}), 200


@app.route("/api/tracking/start", methods=["POST"])
def start_tracking():
    data = request.get_json()
    vehicle_id = data.get("id")
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = True
    return jsonify({"status": "tracking started", "id": vehicle_id}), 200


@app.route("/api/tracking/stop", methods=["POST"])
def stop_tracking():
    data = request.get_json()
    vehicle_id = data.get("id")
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = False
    return jsonify({"status": "tracking stopped", "id": vehicle_id}), 200


@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"


if __name__ == "__main__":
    app.run(debug=True)
