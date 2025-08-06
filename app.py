# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.distance import geodesic
import time

app = Flask(__name__)
CORS(app)

# In-memory store: {vehicle_id: {"lat": 0.0, "lon": 0.0, "last_update": timestamp}}
vehicle_data = {}

@app.route("/api/location/update", methods=["GET"])
def update_location():
    vehicle_id = request.args.get("id")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not all([vehicle_id, lat, lon]):
        return "Missing parameters", 400

    vehicle_data[vehicle_id] = {
        "lat": float(lat),
        "lon": float(lon),
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

        # Simulate ETA: assume 30 km/h average speed, show 5–15 minutes ETA
        eta_min = round(5 + (age / 60))

        results[vehicle_id] = {
            "lat": lat,
            "lon": lon,
            "eta_min": eta_min
        }

    return jsonify(results)
