import os, json, uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_TYPE_ENV = os.getenv("DB_TYPE", "").strip().lower()
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "lookingforhome")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "LookingForHome2026!")
MYSQL_DB = os.getenv("MYSQL_DB", "findhome_singapore")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "findhome.db")
INITIAL_PROPERTIES = [
    {
        "title": "Luxurious 4-Bedroom River Valley Condominium near Great World MRT",
        "subdivision": "Central (CBD, Marina Bay, Orchard)",
        "city": "River Valley",
        "address": "86 River Valley Rd, Singapore 238274",
        "neighborhood": "River Valley",
        "latitude": 1.2934,
        "longitude": 103.8372,
        "total_rent": 6400,
        "bedrooms": 4,
        "bathrooms": 3,
        "surface": 1650,
        "portal": "PropertyGuru SG",
        "url": "https://www.propertyguru.com.sg/listing/river-valley-condo-101",
        "desc": "Olympic swimming pool, tennis court, private lift access, and panoramic city skyline view. 3 minutes to CBD.",
        "contact_name": "Lion City Living",
        "contact_phone": "+65 6555 0192",
        "contact_agency": "Singapore Prime Properties"
    },
    {
        "title": "Chic Heritage Shophouse 3-Bedroom Loft in Tanjong Pagar",
        "subdivision": "Central (CBD, Marina Bay, Orchard)",
        "city": "Tanjong Pagar",
        "address": "48 Duxton Rd, Singapore 089512",
        "neighborhood": "Duxton / Tanjong Pagar",
        "latitude": 1.2785,
        "longitude": 103.8425,
        "total_rent": 5800,
        "bedrooms": 3,
        "bathrooms": 2,
        "surface": 1400,
        "portal": "99.co Singapore",
        "url": "https://www.99.co/singapore/rent/duxton-shophouse",
        "desc": "Restored conservation shophouse with spiral staircase, airwell courtyard, designer kitchen, surrounded by top cafes.",
        "contact_name": "Duxton Heritage Co-Living",
        "contact_phone": "+65 6555 0144",
        "contact_agency": "Island Homes"
    }
]
SUBDIVISIONS = [
    [
        "Central (CBD, Marina Bay, Orchard)",
        "D01-D09"
    ],
    [
        "River Valley & Tanglin",
        "D10"
    ],
    [
        "East Coast & Katong",
        "D15"
    ],
    [
        "Queenstown & Bukit Merah",
        "D03"
    ],
    [
        "Novena & Toa Payoh",
        "D11-D12"
    ]
]
_ACTIVE_ENGINE = None

def detect_engine():
    global _ACTIVE_ENGINE
    if _ACTIVE_ENGINE is not None: return _ACTIVE_ENGINE
    if DB_TYPE_ENV == "sqlite":
        _ACTIVE_ENGINE = "sqlite"
        return _ACTIVE_ENGINE
    try:
        import pymysql
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB, connect_timeout=3)
        conn.close()
        _ACTIVE_ENGINE = "mysql"
        return _ACTIVE_ENGINE
    except Exception:
        _ACTIVE_ENGINE = "sqlite"
        return _ACTIVE_ENGINE

def get_raw_connection():
    if detect_engine() == "mysql":
        import pymysql, pymysql.cursors
        return pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB, charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=False)
    else:
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_raw_connection()
    c = conn.cursor()
    engine = detect_engine()

    if engine == "mysql":
        c.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id VARCHAR(64) PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT,
            city VARCHAR(100) NOT NULL, subdivision VARCHAR(100) NOT NULL, subdivision_code VARCHAR(10),
            address VARCHAR(255), neighborhood VARCHAR(100), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
            total_rent DOUBLE PRECISION NOT NULL, ideal_roommates INT DEFAULT 4, bedrooms INT NOT NULL, bathrooms INT NOT NULL,
            surface INT NOT NULL, has_elevator TINYINT(1) DEFAULT 1, is_exterior TINYINT(1) DEFAULT 1, is_furnished TINYINT(1) DEFAULT 1,
            has_terrace TINYINT(1) DEFAULT 0, has_air_con TINYINT(1) DEFAULT 0, source_portal VARCHAR(100), source_url VARCHAR(500),
            property_type VARCHAR(50) DEFAULT 'apartment', images JSON, contact_name VARCHAR(150), contact_phone VARCHAR(50),
            contact_agency VARCHAR(150), status VARCHAR(30) DEFAULT 'available', created_at VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INT AUTO_INCREMENT PRIMARY KEY, ip VARCHAR(64), country VARCHAR(100), country_code VARCHAR(10),
            region VARCHAR(100), city VARCHAR(100), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
            path VARCHAR(255), method VARCHAR(10), status_code INT, user_agent TEXT, device_type VARCHAR(30),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_logs (
            id INT AUTO_INCREMENT PRIMARY KEY, sender_phone VARCHAR(50), sender_name VARCHAR(100),
            message_body TEXT, response_body TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        c.execute("SELECT COUNT(*) as cnt FROM properties")
        row = c.fetchone()
        cnt = row["cnt"] if isinstance(row, dict) else row[0]
        if cnt == 0:
            seed_data(c, engine)
            conn.commit()
    else:
        c.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, city TEXT NOT NULL,
            subdivision TEXT NOT NULL, subdivision_code TEXT, address TEXT, neighborhood TEXT,
            latitude REAL, longitude REAL, total_rent REAL NOT NULL, ideal_roommates INTEGER DEFAULT 4,
            bedrooms INTEGER NOT NULL, bathrooms INTEGER NOT NULL, surface INTEGER NOT NULL,
            has_elevator INTEGER DEFAULT 1, is_exterior INTEGER DEFAULT 1, is_furnished INTEGER DEFAULT 1,
            has_terrace INTEGER DEFAULT 0, has_air_con INTEGER DEFAULT 0, source_portal TEXT,
            source_url TEXT, property_type TEXT, images TEXT, contact_name TEXT, contact_phone TEXT,
            contact_agency TEXT, status TEXT DEFAULT 'available', created_at TEXT
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, country TEXT, country_code TEXT, region TEXT,
            city TEXT, latitude REAL, longitude REAL, path TEXT, method TEXT, status_code INTEGER,
            user_agent TEXT, device_type TEXT, timestamp TEXT
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sender_phone TEXT, sender_name TEXT,
            message_body TEXT, response_body TEXT, timestamp TEXT
        );
        """)
        conn.commit()
        c.execute("SELECT COUNT(*) FROM properties")
        if c.fetchone()[0] == 0:
            seed_data(c, engine)
            conn.commit()
    conn.close()

def seed_data(c, engine):
    now = datetime.now(timezone.utc).isoformat()
    imgs = json.dumps(["static/images/prop-mad-01-1.jpg"])
    for idx, p in enumerate(INITIAL_PROPERTIES):
        pid = f"singapore-prop-{idx+1:02d}"
        if engine == "mysql":
            c.execute("""
            INSERT INTO properties (id, title, description, city, subdivision, subdivision_code, address, neighborhood,
            latitude, longitude, total_rent, ideal_roommates, bedrooms, bathrooms, surface, source_portal, source_url,
            images, contact_name, contact_phone, contact_agency, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (pid, p["title"], p["desc"], p["city"], p["subdivision"], p.get("subdivision_code", ""),
                  p["address"], p["neighborhood"], p["latitude"], p["longitude"], p["total_rent"],
                  p["bedrooms"], p["bedrooms"], p["bathrooms"], p["surface"], p["portal"], p["url"],
                  imgs, p["contact_name"], p["contact_phone"], p["contact_agency"], "available", now))
        else:
            c.execute("""
            INSERT INTO properties (id, title, description, city, subdivision, subdivision_code, address, neighborhood,
            latitude, longitude, total_rent, ideal_roommates, bedrooms, bathrooms, surface, source_portal, source_url,
            images, contact_name, contact_phone, contact_agency, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, p["title"], p["desc"], p["city"], p["subdivision"], p.get("subdivision_code", ""),
                  p["address"], p["neighborhood"], p["latitude"], p["longitude"], p["total_rent"],
                  p["bedrooms"], p["bedrooms"], p["bathrooms"], p["surface"], p["portal"], p["url"],
                  imgs, p["contact_name"], p["contact_phone"], p["contact_agency"], "available", now))

def get_properties(city=None, subdivision=None, portal=None, min_bedrooms=None, max_total_rent=None):
    conn = get_raw_connection()
    c = conn.cursor()
    q = "SELECT * FROM properties WHERE 1=1"
    params = []
    if city:
        q += " AND LOWER(city) LIKE %s" if detect_engine() == "mysql" else " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()}%")
    if subdivision:
        q += " AND (LOWER(subdivision) LIKE %s OR LOWER(subdivision_code) LIKE %s)" if detect_engine() == "mysql" else " AND (LOWER(subdivision) LIKE ? OR LOWER(subdivision_code) LIKE ?)"
        params.extend([f"%{subdivision.lower()}%", f"%{subdivision.lower()}%"])
    if portal:
        q += " AND LOWER(source_portal) LIKE %s" if detect_engine() == "mysql" else " AND LOWER(source_portal) LIKE ?"
        params.append(f"%{portal.lower()}%")
    if min_bedrooms:
        q += " AND bedrooms >= %s" if detect_engine() == "mysql" else " AND bedrooms >= ?"
        params.append(int(min_bedrooms))
    if max_total_rent:
        q += " AND total_rent <= %s" if detect_engine() == "mysql" else " AND total_rent <= ?"
        params.append(float(max_total_rent))

    q += " ORDER BY total_rent ASC"
    c.execute(q, tuple(params))
    rows = c.fetchall()
    res = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("images"), str):
            try: d["images"] = json.loads(d["images"])
            except Exception: d["images"] = []
        d["rent_per_person"] = round(d["total_rent"] / max(1, d.get("ideal_roommates", d.get("bedrooms", 4))))
        res.append(d)
    conn.close()
    return res

def record_access_log(ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type):
    try:
        conn = get_raw_connection()
        c = conn.cursor()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if detect_engine() == "mysql":
            c.execute("""
            INSERT INTO access_logs (ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type))
        else:
            c.execute("""
            INSERT INTO access_logs (ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, now))
        conn.commit()
        conn.close()
    except Exception: pass

def get_access_logs(limit=100):
    conn = get_raw_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM access_logs ORDER BY id DESC LIMIT {int(limit)}")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
