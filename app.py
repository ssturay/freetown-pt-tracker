from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.distance import geodesic
import time
import config  # <-- Stores ADMIN_PASSWORD

app = Flask(__name__)
CORS(app)

# In-memory store: {vehicle_id: {"lat": ..., "lon": ..., "last_update": ..., "mode": ...}}
vehicle_data = {}

# In-memory store for tracking status: {vehicle_id: bool}
tracking_status = {}

# ---------- LOGIN ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    password = data.get("password") if data else None
    if not password:
        return jsonify({"success": False, "message": "Password is required"}), 400
    if password == config.ADMIN_PASSWORD:
        return jsonify({"success": True, "message": "Login successful"}), 200
    return jsonify({"success": False, "message": "Invalid password"}), 401


# ---------- VEHICLE LOCATION UPDATE ----------
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


# ---------- VEHICLE LIST ----------
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    vehicles = []

    # Optional: Calculate ETA if user location is provided
    user_lat = request.args.get("user_lat", type=float)
    user_lon = request.args.get("user_lon", type=float)
    has_user_location = user_lat is not None and user_lon is not None

    for vehicle_id, info in vehicle_data.items():
        if not tracking_status.get(vehicle_id, False):
            continue

        lat, lon = info["lat"], info["lon"]
        age = now - info["last_update"]

        eta_min = round(5 + (age / 60))  # Placeholder ETA
        distance_m = None

        if has_user_location:
            distance_m = round(geodesic((user_lat, user_lon), (lat, lon)).meters)
            if distance_m > 0:
                eta_min = round(distance_m / (1.4 * 60))  # walking speed ~1.4 m/s

        vehicles.append({
            "id": vehicle_id,
            "lat": lat,
            "lon": lon,
            "mode": info.get("mode", "unknown"),
            "eta_min": eta_min,
            "distance_m": distance_m
        })

    return jsonify({"vehicles": vehicles})


# ---------- HOME ----------
@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"


# ---------- CLEAR VEHICLES ----------
@app.route("/api/vehicles/clear", methods=["POST"])
def clear_vehicles():
    global vehicle_data
    vehicle_data = {}
    return jsonify({"status": "cleared", "message": "All vehicles have been removed"}), 200


# ---------- START TRACKING ----------
@app.route("/api/tracking/start", methods=["POST"])
def start_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = True
    return jsonify({"status": "tracking started", "id": vehicle_id}), 200


# ---------- STOP TRACKING ----------
@app.route("/api/tracking/stop", methods=["POST"])
def stop_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None
    if not vehicle_id:
        return jsonify({"error": "Missing vehicle id"}), 400
    tracking_status[vehicle_id] = False
    return jsonify({"status": "tracking stopped", "id": vehicle_id}), 200


if __name__ == '__main__':
    app.run(debug=True)
