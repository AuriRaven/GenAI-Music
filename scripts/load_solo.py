import os
import re
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# === LOAD ENV VARIABLES ===
load_dotenv(encoding='utf-8')

BASE_DIR = r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\bach_midis_solo_all"

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "dbname": os.getenv("PG_DBNAME"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD")
}

# === CONNECT TO POSTGRES ===
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# === CREATE TABLES ===
cur.execute("""
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id SERIAL PRIMARY KEY,
    instrument_name TEXT NOT NULL UNIQUE
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS works (
    work_id SERIAL PRIMARY KEY,
    instrument_id INT REFERENCES instruments(instrument_id),
    bwv TEXT NOT NULL,
    title TEXT NOT NULL,
    key TEXT,
    folder_path TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS movements (
    movement_id SERIAL PRIMARY KEY,
    work_id INT REFERENCES works(work_id),
    movement_number INT,
    movement_name TEXT NOT NULL,
    midi_file_path TEXT NOT NULL
);
""")
conn.commit()

def get_instrument_id(name):
    cur.execute("SELECT instrument_id FROM instruments WHERE instrument_name=%s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO instruments (instrument_name) VALUES (%s) RETURNING instrument_id;", (name,))
    return cur.fetchone()[0]

# === SCAN FOLDERS AND INSERT ===
for instrument_folder in os.listdir(BASE_DIR):
    instrument_path = os.path.join(BASE_DIR, instrument_folder)
    if not os.path.isdir(instrument_path):
        continue

    instrument_id = get_instrument_id(instrument_folder)

    for work_folder in os.listdir(instrument_path):
        work_path = os.path.join(instrument_path, work_folder)
        if not os.path.isdir(work_path):
            continue

        # extract BWV, title, key
        m = re.match(r"(BWV\d+)\s+(.*)\s+in\s+(.*)", work_folder)
        if m:
            bwv, title, key = m.groups()
        else:
            parts = work_folder.split(" ",1)
            bwv = parts[0] if parts else work_folder
            title = work_folder
            key = None

        cur.execute("""
            INSERT INTO works (instrument_id,bwv,title,key,folder_path)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING work_id;
        """, (instrument_id,bwv,title,key,work_path))
        work_id = cur.fetchone()[0]

        midi_files = [f for f in os.listdir(work_path) if f.lower().endswith(".mid")]
        for idx, midi in enumerate(sorted(midi_files), start=1):
            movement_name = os.path.splitext(midi)[0]
            midi_path = os.path.join(work_path, midi)
            cur.execute("""
                INSERT INTO movements (work_id,movement_number,movement_name,midi_file_path)
                VALUES (%s,%s,%s,%s)
            """,(work_id,idx,movement_name,midi_path))

conn.commit()
cur.close()
conn.close()
print("Database filled successfully ✅")
