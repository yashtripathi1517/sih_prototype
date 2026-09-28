import sqlite3
import random
from datetime import datetime, timedelta

def setup_db():
    print("Initializing SQLite Database...")
    conn = sqlite3.connect('anpr.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles
                 (id INTEGER PRIMARY KEY, plate_number TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cameras
                 (id INTEGER PRIMARY KEY, name TEXT, latitude REAL, longitude REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY, vehicle_id INTEGER, camera_id INTEGER, timestamp DATETIME,
                 FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
                 FOREIGN KEY(camera_id) REFERENCES cameras(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY, vehicle_id INTEGER, type TEXT, description TEXT, timestamp DATETIME,
                 FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))''')

    # Clear existing data (for clean re-runs)
    c.execute('DELETE FROM alerts')
    c.execute('DELETE FROM events')
    c.execute('DELETE FROM cameras')
    c.execute('DELETE FROM vehicles')

    # Generate 20 Cameras around a base location (New Delhi)
    base_lat, base_lon = 28.6139, 77.2090
    cameras = []
    print("Generating synthetic cameras...")
    for i in range(20):
        lat = base_lat + random.uniform(-0.1, 0.1)
        lon = base_lon + random.uniform(-0.1, 0.1)
        c.execute('INSERT INTO cameras (name, latitude, longitude) VALUES (?, ?, ?)', (f'Cam-{i+1:02d}', lat, lon))
        cameras.append(i+1)

    # Generate 150 Vehicles
    vehicles = []
    print("Generating synthetic vehicle data...")
    for i in range(150):
        plate = f'DL{random.randint(1,14):02d}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.randint(1000,9999)}'
        try:
            c.execute('INSERT INTO vehicles (plate_number) VALUES (?)', (plate,))
            vehicles.append((i+1, plate))
        except sqlite3.IntegrityError:
            pass # Ignore random duplicates

    # Generate ANPR Events (5 to 30 events per vehicle)
    now = datetime.now()
    print("Generating synthetic trajectory events...")
    for v_id, plate in vehicles:
        num_events = random.randint(5, 30)
        current_time = now - timedelta(days=2)
        for _ in range(num_events):
            cam_id = random.choice(cameras)
            current_time += timedelta(minutes=random.randint(5, 120))
            c.execute('INSERT INTO events (vehicle_id, camera_id, timestamp) VALUES (?, ?, ?)', (v_id, cam_id, current_time.strftime("%Y-%m-%d %H:%M:%S")))

    # Generate Alerts (Random pattern detections)
    print("Generating synthetic alerts...")
    alert_types = ['Stalking Detected', 'High-Speed Movement', 'Unusual Pattern', 'Blacklisted Vehicle']
    for _ in range(40):
        v_id, plate = random.choice(vehicles)
        a_type = random.choice(alert_types)
        t = now - timedelta(hours=random.randint(1, 48))
        c.execute('INSERT INTO alerts (vehicle_id, type, description, timestamp) VALUES (?, ?, ?, ?)',
                  (v_id, a_type, f'Vehicle {plate} flagged for {a_type.lower()}.', t.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    
    print("Database setup complete! 'anpr.db' has been created successfully.")
    
    # Print sample queries for testing
    print("\nSample Plate Numbers to search:")
    sample_plates = [v[1] for v in random.sample(vehicles, 5)]
    for p in sample_plates:
        print(f" - {p}")

if __name__ == '__main__':
    setup_db()