from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import os
import setup_database

app = FastAPI(title="ANPR Trajectory Tracking API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'anpr.db')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

def get_db_connection():
    """Helper function to get a database connection, auto-creating DB if missing."""
    if not os.path.exists(DB_FILE):
        print("Database file missing. Auto-generating synthetic data...")
        setup_database.setup_db()
        
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the frontend HTML file."""
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")

@app.get("/api/stats")
async def get_stats():
    """Get high-level statistics for the dashboard."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as count FROM vehicles")
    total_vehicles = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM cameras")
    total_cameras = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM alerts")
    total_alerts = c.fetchone()['count']
    
    conn.close()
    
    return {
        "total_vehicles": total_vehicles,
        "total_cameras": total_cameras,
        "total_alerts": total_alerts
    }

@app.get("/api/vehicle/{plate_number}")
async def get_vehicle_trajectory(plate_number: str):
    """Retrieve trajectory data (sequence of camera events) for a specific vehicle."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Find the vehicle by plate number
    c.execute("SELECT id FROM vehicles WHERE plate_number = ?", (plate_number,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    vehicle_id = vehicle['id']
    
    # Fetch trajectory ordered by timestamp
    query = """
        SELECT e.timestamp, c.name as camera_name, c.latitude, c.longitude
        FROM events e
        JOIN cameras c ON e.camera_id = c.id
        WHERE e.vehicle_id = ?
        ORDER BY e.timestamp ASC
    """
    c.execute(query, (vehicle_id,))
    rows = c.fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries
    trajectory = [dict(row) for row in rows]
    
    return {
        "plate_number": plate_number,
        "trajectory": trajectory
    }

@app.get("/api/alerts")
async def get_alerts():
    """Retrieve recent pattern detection alerts."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT a.type, a.description, a.timestamp, v.plate_number
        FROM alerts a
        JOIN vehicles v ON a.vehicle_id = v.id
        ORDER BY a.timestamp DESC
        LIMIT 20
    """
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/cameras")
async def get_cameras():
    """Retrieve all camera locations for mapping."""
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM cameras"
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]