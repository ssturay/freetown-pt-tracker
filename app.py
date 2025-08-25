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
            role TEXT,
            lat REAL,
            lon REAL,
            route_id TEXT,
            sharing INTEGER DEFAULT 0,
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
    c.execute("SELECT id, role, lat, lon, route_id, sharing, timestamp FROM vehicles")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        vehicles_data[row[0]] = {
            "id": row[0],
            "role": row[1],
            "lat": row[2],
            "lon": row[3],
            "route_id": row[4],
            "sharing": bool(row[5]),
            "timestamp": row[6]
        }

# =========================
# Save a single vehicle to DB
# =========================
def save_to_db(vehicle):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles (id, role, lat, lon, route_id, sharing, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            role=excluded.role,
            lat=excluded.lat,
            lon=excluded.lon,
            route_id=excluded.route_id,
            sharing=excluded.sharing,
            timestamp=excluded.timestamp
    """, (
        vehicle["id"],
        vehicle["role"],
        vehicle["lat"],
        vehicle["lon"],
        vehicle["route_id"],
        1 if vehicle["sharing"] else 0,
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

    # Only return vehicles that are actively sharing
    vehicles_list = [v for v in vehicles_list if v.get("sharing")]

    return jsonify({"vehicles": vehicles_list})

# =========================
# API: Update a vehicle
# =========================
@app.route("/api/update_vehicle", methods=["POST"])
def update_vehicle():
    data = request.get_json(force=True)

    vehicle_id = str(data.get("id", "")).strip()
    role = str(data.get("role", "")).strip()
    lat = data.get("lat")
    lon = data.get("lon")
    route_id = str(data.get("route_id", "")).strip()
    sharing = 1 if data.get("sharing") else 0

    if not vehicle_id or lat is None or lon is None or not role:
        return jsonify({"error": "Missing required fields"}), 400

    vehicle = {
        "id": vehicle_id,
        "role": role,
        "lat": float(lat),
        "lon": float(lon),
        "route_id": route_id if route_id else None,
        "sharing": sharing,
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
