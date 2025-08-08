from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# In-memory store: {vehicle_id: {"lat": ..., "lon": ..., "mode": ..., "last_update": ...}}
vehicle_data = {}

@app.route("/api/location/update", methods=["GET"])
def update_location():
    vehicle_id = request.args.get("id")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    mode = request.args.get("mode")

    if not all([vehicle_id, lat, lon, mode]):
        return "Missing parameters (id, lat, lon, mode required)", 400

    vehicle_data[vehicle_id] = {
        "lat": float(lat),
        "lon": float(lon),
        "mode": mode.strip().lower(),  # normalize mode
        "last_update": time.time()
    }
    return f"Location updated for {vehicle_id}", 200

@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    results = {}

    for vehicle_id, info in vehicle_data.items():
        lat = info["lat"]
        lon = info["lon"]
        mode = info.get("mode", "unknown")
        age = now - info["last_update"]

        # Simulated ETA: assume 30 km/h avg, just a placeholder
        eta_min = round(5 + (age / 60))

        results[vehicle_id] = {
            "lat": lat,
            "lon": lon,
            "mode": mode,
            "eta_min": eta_min
        }

    return jsonify(results)

@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"
