# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.distance import geodesic
import time

app = Flask(__name__)
CORS(app)

# In-memory store: {vehicle_id: {"lat": ..., "lon": ..., "last_update": ..., "mode": ...}}
vehicle_data = {}

@app.route("/api/location/update", methods=["GET"])
def update_location():
    vehicle_id = request.args.get("id")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    mode = request.args.get("mode")  # NEW

    if not all([vehicle_id, lat, lon, mode]):
        return "Missing parameters", 400

    vehicle_data[vehicle_id] = {
        "lat": float(lat),
        "lon": float(lon),
        "mode": mode.strip().lower(),  # Normalize
        "last_update": time.time()
    }

    return f"Location updated for {vehicle_id}", 200

@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    results = {}

    for vehicle_id, info in vehicle_data.items():
        lat, lon = info["lat"], info["lon"]
        age = now - info["last_update"]

        # Simulate ETA: assume 30 km/h average speed, estimate
        eta_min = round(5 + (age / 60))  # Just an estimate

        results[vehicle_id] = {
            "lat": lat,
            "lon": lon,
            "mode": info.get("mode", "unknown"),  # NEW
            "eta_min": eta_min
        }

    return jsonify(results)

@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"

@app.route("/api/location/delete", methods=["POST"])
def delete_vehicle():
    vehicle_id = request.json.get("id")
    if not vehicle_id:
        return "Vehicle ID required", 400

    if vehicle_id in vehicle_data:
        del vehicle_data[vehicle_id]
        return f"Deleted vehicle {vehicle_id}", 200
    else:
        return "Vehicle not found", 404
