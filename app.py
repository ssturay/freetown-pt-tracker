from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# In-memory vehicle storage: {vehicle_id: {...}}
vehicle_data = {}

# Tracking sessions: {vehicle_id: {"active": bool, "last_active": timestamp}}
tracking_status = {}

# Mode → Icon mapping
ICON_MAP = {
    "podapoda": "https://cdn-icons-png.flaticon.com/512/743/743007.png",
    "taxi": "https://cdn-icons-png.flaticon.com/512/190/190671.png",
    "keke": "https://cdn-icons-png.flaticon.com/512/2967/2967037.png",
    "paratransit bus": "https://cdn-icons-png.flaticon.com/512/61/61221.png",
    "waka fine bus": "https://cdn-icons-png.flaticon.com/512/861/861060.png",
    "motorbike": "https://cdn-icons-png.flaticon.com/512/4721/4721203.png"
}

TRACKING_TIMEOUT = 300  # 5 minutes in seconds


@app.route("/", methods=["GET"])
def home():
    return "✅ Public Transport Tracker backend is running!"


@app.route("/api/location/update", methods=["GET"])
def update_location():
    vehicle_id = request.args.get("id")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    mode = request.args.get("mode")

    if not all([vehicle_id, lat, lon, mode]):
        return jsonify({"success": False, "message": "Missing parameters"}), 400

    vehicle_data[vehicle_id] = {
        "lat": float(lat),
        "lon": float(lon),
        "mode": mode.strip().lower(),
        "last_update": time.time()
    }

    # Keep last_active fresh if tracking is on
    if tracking_status.get(vehicle_id, {}).get("active"):
        tracking_status[vehicle_id]["last_active"] = time.time()

    return jsonify({"success": True, "message": f"Location updated for {vehicle_id}"}), 200


@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    now = time.time()
    vehicles = []

    for vehicle_id, info in vehicle_data.items():
        # Skip if tracking session expired
        if tracking_status.get(vehicle_id, {}).get("active"):
            if now - tracking_status[vehicle_id]["last_active"] > TRACKING_TIMEOUT:
                tracking_status[vehicle_id]["active"] = False

        lat, lon = info["lat"], info["lon"]
        age = now - info["last_update"]

        vehicles.append({
            "id": vehicle_id,
            "lat": lat,
            "lon": lon,
            "mode": info.get("mode", "unknown"),
            "icon": ICON_MAP.get(info.get("mode", ""), ""),
            "eta_min": round(5 + (age / 60))
        })

    return jsonify({"success": True, "vehicles": vehicles}), 200


@app.route("/api/tracking/start", methods=["POST"])
def start_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None

    if not vehicle_id:
        return jsonify({"success": False, "message": "Missing vehicle id"}), 400

    tracking_status[vehicle_id] = {"active": True, "last_active": time.time()}

    return jsonify({"success": True, "message": "Tracking started", "id": vehicle_id}), 200


@app.route("/api/tracking/stop", methods=["POST"])
def stop_tracking():
    data = request.get_json()
    vehicle_id = data.get("id") if data else None

    if not vehicle_id:
        return jsonify({"success": False, "message": "Missing vehicle id"}), 400

    tracking_status[vehicle_id] = {"active": False, "last_active": time.time()}

    return jsonify({"success": True, "message": "Tracking stopped", "id": vehicle_id}), 200


@app.route("/api/vehicles/clear", methods=["POST"])
def clear_vehicles():
    global vehicle_data
    vehicle_data = {}
    return jsonify({"success": True, "message": "All vehicles have been removed"}), 200


if __name__ == '__main__':
    app.run(debug=True)
