from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
from datetime import datetime
from config import API_KEY, DB_PATH, VEHICLE_STALE_SECONDS, MIN_UPDATE_INTERVAL

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # adjust origin in production

# =========================
# In-memory store
# =========================
vehicles_mem = {}  # { vehicle_id: {mode, lat, lon, last_update} }
last_update_times = {}  # { vehicle_id: timestamp }


# =========================
# Database setup
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY,
                mode TEXT,
                lat REAL,
                lon REAL,
                last_update INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stops (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lon REAL
            )
        """)
    print("[DB] Initialized.")

def load_vehicles_from_db():
    """Load recent vehicle positions from DB into memory."""
    cutoff = int(time.time()) - VEHICLE_STALE_SECONDS
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM vehicles WHERE last_update >= ?", (cutoff,)).fetchall()
    for row in rows:
        vehicles_mem[row["id"]] = {
            "mode": row["mode"],
            "lat": row["lat"],
            "lon": row["lon"],
            "last_update": row["last_update"]
        }
    print(f"[DB] Loaded {len(vehicles_mem)} vehicles into memory.")


# =========================
# Helpers
# =========================
def cleanup_stale():
    """Remove stale vehicles from both memory and DB."""
    cutoff = int(time.time()) - VEHICLE_STALE_SECONDS
    stale_ids = [vid for vid, v in vehicles_mem.items() if v["last_update"] < cutoff]
    for vid in stale_ids:
        vehicles_mem.pop(vid, None)
        last_update_times.pop(vid, None)
    with get_db() as conn:
        conn.execute("DELETE FROM vehicles WHERE last_update < ?", (cutoff,))
    if stale_ids:
        print(f"[Cleanup] Removed {len(stale_ids)} stale vehicles.")

def update_vehicle_in_db(vehicle_id, mode, lat, lon):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO vehicles (id, mode, lat, lon, last_update)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                mode=excluded.mode,
                lat=excluded.lat,
                lon=excluded.lon,
                last_update=excluded.last_update
        """, (vehicle_id, mode, lat, lon, int(time.time())))


# =========================
# API Routes
# =========================
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    cleanup_stale()
    return jsonify({"vehicles": [
        {"id": vid, **data} for vid, data in vehicles_mem.items()
    ]})

@app.route("/api/location/update", methods=["POST"])
def update_location():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    vid = str(data.get("id", "")).strip()
    mode = str(data.get("mode", "")).strip().lower()
    lat = data.get("lat")
    lon = data.get("lon")

    if not vid or not mode or lat is None or lon is None:
        return jsonify({"error": "Missing required fields"}), 400

    now = time.time()
    if vid in last_update_times and now - last_update_times[vid] < MIN_UPDATE_INTERVAL:
        return jsonify({"status": "ignored", "reason": "rate limit"}), 429

    vehicles_mem[vid] = {"mode": mode, "lat": lat, "lon": lon, "last_update": int(now)}
    last_update_times[vid] = now
    update_vehicle_in_db(vid, mode, lat, lon)

    return jsonify({"status": "success", "vehicle": vehicles_mem[vid]})

@app.route("/api/stops", methods=["GET"])
def get_stops():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM stops").fetchall()
    stops = [{"id": row["id"], "name": row["name"], "lat": row["lat"], "lon": row["lon"]} for row in rows]
    return jsonify({"stops": stops})


# =========================
# Main entry
# =========================
if __name__ == "__main__":
    init_db()
    load_vehicles_from_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
