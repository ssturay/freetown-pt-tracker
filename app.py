from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import threading
import time

app = Flask(__name__)
CORS(app)

DB_FILE = "vehicles.db"
vehicles_data = {}  # {vehicle_id: {...}}

# =========================
# Database Initialization
# =========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            mode TEXT,
            lat REAL,
            lon REAL,
            route_id TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

# =========================
# Load data from DB to memory
# =========================
def load_from_db():
    global vehicles_data
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, mode, lat, lon, route_id, timestamp FROM vehicles")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        vehicles_data[row[0]] = {
            "id": row[0],
            "mode": row[1],
            "lat": row[2],
            "lon": row[3],
            "route_id": row[4],
            "timestamp": row[5]
        }

# =========================
# Save a single vehicle to DB
# =========================
def save_to_db(vehicle):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles (id, mode, lat, lon, route_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            mode=excluded.mode,
            lat=excluded.lat,
            lon=excluded.lon,
            route_id=excluded.route_id,
            timestamp=excluded.timestamp
    """, (
        vehicle["id"],
        vehicle["mode"],
        vehicle["lat"],
        vehicle["lon"],
        vehicle["route_id"],
        vehicle["timestamp"]
    ))
    conn.commit()
    conn.close()

# =========================
# API: Get all vehicles (optional route filter)
# =========================
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    route_filter = request.args.get("route_id", "").strip()
    now = time.time()

    # Remove stale entries (older than 30 seconds)
    expired = [vid for vid, v in vehicles_data.items() if now - v["timestamp"] > 30]
    for vid in expired:
        del vehicles_data[vid]

    vehicles_list = list(vehicles_data.values())

    # Apply route_id filter if provided
    if route_filter:
        vehicles_list = [v for v in vehicles_list if v.get("route_id") == route_filter]

    # Return only vehicles with a route_id
    vehicles_list = [v for v in vehicles_list if v.get("route_id")]

    return jsonify({"vehicles": vehicles_list})

# =========================
# API: Update a vehicle
# =========================
@app.route("/api/update_vehicle", methods=["POST"])
def update_vehicle():
    data = request.get_json(force=True)

    vehicle_id = str(data.get("id", "")).strip()
    mode = str(data.get("mode", "")).strip().lower()
    lat = data.get("lat")
    lon = data.get("lon")
    route_id = str(data.get("route_id", "")).strip()

    if not vehicle_id or lat is None or lon is None or not mode:
        return jsonify({"error": "Missing required fields"}), 400

    vehicle = {
        "id": vehicle_id,
        "mode": mode,
        "lat": float(lat),
        "lon": float(lon),
        "route_id": route_id if route_id else None,
        "timestamp": time.time()
    }

    # Update in-memory store
    vehicles_data[vehicle_id] = vehicle

    # Save to DB
    save_to_db(vehicle)

    return jsonify({"status": "success", "vehicle": vehicle})

# =========================
# Cleanup Thread (DB + Memory)
# =========================
def cleanup_thread():
    while True:
        now = time.time()
        expired = [vid for vid, v in vehicles_data.items() if now - v["timestamp"] > 600]  # 10 min
        for vid in expired:
            del vehicles_data[vid]

        # Also remove from DB
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        cutoff = now - 600
        c.execute("DELETE FROM vehicles WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

        time.sleep(60)

# =========================
# Startup
# =========================
if __name__ == "__main__":
    init_db()
    load_from_db()
    threading.Thread(target=cleanup_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
