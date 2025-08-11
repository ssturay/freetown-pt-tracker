from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.distance import geodesic
import time
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# In-memory store: {vehicle_id: {"lat": ..., "lon": ..., "last_update": ..., "mode": ...}}
vehicle_data = {}

# Tracking status: {vehicle_id: bool}
tracking_status = {}

# Simple hardcoded credentials
VALID_USERNAME = "admin"
VALID_PASSWORD = "mypassword"


# -------------------- LOGIN --------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401


# -------------------- LOCATION UPDATE --------------------
@app.route("/api/location/update", methods=["GET"])
def update_location():
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


# -------------------- GET ALL VEHICLES --------------------
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    vehicles = []

    for vehicle_id, info in vehicle_data.items():
        lat, lon = info["lat"], info["lon"]
        age = now - info["last_update"]

        # Placeholder ETA (1–15 min range)
        eta_min = random.randint(1, 15)

        vehicles.append({
            "id": vehicle_id,
            "lat": lat,
            "lon": lon,
            "mode": info.get("mode", "unknown"),
            "eta_min": eta_min,
            "last_update_sec": round(age)
        })

    return jsonify({"vehicles": vehicles})


# -------------------- GET SPECIFIC VEHICLE --------------------
@app.route("/api/vehicle/<vehicle_id>", methods=["GET"])
def get_vehicle(vehicle_id):
    info = vehicle_data.get(vehicle_id)
    if not info:
        return jsonify({"error": "Vehicle not found"}), 404

    now = time.time()
    age = now - info["last_update"]

    return jsonify({
        "id": vehicle_id,
        "lat": info["lat"],
        "lon": info["lon"],
        "mode": info.get("mode", "unknown"),
        "last_update_sec": round(age)
    })


# -------------------- CLEAR VEHICLES --------------------
@app.route("/api/vehicles/clear", methods=["POST"])
def clear_vehicles():
    global vehicle_data
    vehicle_data = {}
    return jsonify({"status": "cleared", "message": "All vehicles have been removed"}), 200


# -------------------- TRACKING CONTROL --------------------
@app.route("/api/tracking/start", methods=["POST"])
def start_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = True
    return jsonify({"status": "tracking started", "id": vehicle_id}), 200


@app.route("/api/tracking/stop", methods=["POST"])
def stop_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = False
    return jsonify({"status": "tracking stopped", "id": vehicle_id}), 200


# -------------------- HOME --------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"


if __name__ == '__main__':
    app.run(debug=True)
