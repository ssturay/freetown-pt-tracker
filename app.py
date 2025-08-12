from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import threading
import time

app = Flask(__name__)
CORS(app)

DB_FILE = "vehicles.db"
vehicles_data = {}  # in-memory store: {vehicle_id: {...}}

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
    c.execute("SELECT id, mode, lat, lon, timestamp FROM vehicles")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        vehicles_data[row[0]] = {
            "id": row[0],
            "mode": row[1],
            "lat": row[2],
            "lon": row[3],
            "timestamp": row[4]
        }

# =========================
# Save a single vehicle to DB
# =========================
def save_to_db(vehicle):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles (id, mode, lat, lon, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            mode=excluded.mode,
            lat=excluded.lat,
            lon=excluded.lon,
            timestamp=excluded.timestamp
    """, (vehicle["id"], vehicle["mode"], vehicle["lat"], vehicle["lon"], vehicle["timestamp"]))
    conn.commit()
    conn.close()

# =========================
# API: Get all vehicles
# =========================
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    return jsonify({"vehicles": list(vehicles_data.values())})

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

    if not vehicle_id or lat is None or lon is None:
        return jsonify({"error": "Missing required fields"}), 400

    vehicle = {
        "id": vehicle_id,
        "mode": mode,
        "lat": float(lat),
        "lon": float(lon),
        "timestamp": time.time()
    }

    # Update in-memory
    vehicles_data[vehicle_id] = vehicle

    # Save to DB
    save_to_db(vehicle)

    return jsonify({"status": "success", "vehicle": vehicle})

# =========================
# Clean up old entries
# =========================
def cleanup_thread():
    while True:
        now = time.time()
        expired = [vid for vid, v in vehicles_data.items() if now - v["timestamp"] > 600]  # older than 10 min
        for vid in expired:
            del vehicles_data[vid]
        time.sleep(60)

# =========================
# Startup
# =========================
if __name__ == "__main__":
    init_db()
    load_from_db()
    threading.Thread(target=cleanup_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
