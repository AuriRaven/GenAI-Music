import os
import re
import psycopg2
from dotenv import load_dotenv

# === LOAD ENV VARIABLES ===
load_dotenv()

BASE_DIR = r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data"
DEFAULT_INSTRUMENT = "Cello"  # fallback

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
    bwv TEXT,
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
    xml_file_path TEXT NOT NULL
);
""")
conn.commit()

# === Folder-to-instrument mapping ===
FOLDER_TO_INSTRUMENT = {
    r"Partita No\. 1.*BWV1002": "Violin",
    r"Partita No\. 2.*BWV1004": "Violin",
    r"Partita No\. 3.*BWV1006": "Violin",
    r"Partita in A minor.*BWV1013": "Flute",
    r"Sonata No\. 1.*BWV1001": "Violin",
    r"Sonata No\. 2.*BWV1003": "Violin",
    r"Sonata No\. 3.*BWV1005": "Violin",
    r"Suite No\. 1.*BWV1007": "Cello",
    r"Suite No\. 2.*BWV1008": "Cello",
    r"Suite No\. 3.*BWV1009": "Cello",
    r"Suite No\. 4.*BWV1010": "Cello",
    r"Suite No\. 5.*BWV1011": "Cello",
    r"Suite No\. 6.*BWV1012": "Cello"
}

def get_instrument_id(name: str) -> int:
    """
    Get the ID of an instrument from the instruments table.
    If the instrument does not exist, insert it and return the new ID.
    
    Args:
        name (str): The name of the instrument.
    
    Returns:
        int: The instrument_id from the database.
    """
    cur.execute("SELECT instrument_id FROM instruments WHERE instrument_name=%s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO instruments (instrument_name) VALUES (%s) RETURNING instrument_id;", (name,))
    return cur.fetchone()[0]

def infer_instrument_from_folder(folder_name: str) -> str:
    """
    Determine the instrument of a work based on its folder name using regex mapping.
    Falls back to DEFAULT_INSTRUMENT if no pattern matches.
    
    Args:
        folder_name (str): The folder name of the work.
    
    Returns:
        str: The inferred instrument name.
    """
    for pattern, instrument in FOLDER_TO_INSTRUMENT.items():
        if re.match(pattern, folder_name):
            print(f"   Folder '{folder_name}' matched pattern '{pattern}' → instrument: {instrument}")
            return instrument
    print(f"   Folder '{folder_name}' did not match any pattern → defaulting to {DEFAULT_INSTRUMENT}")
    return DEFAULT_INSTRUMENT

# === SCAN WORK FOLDERS AND INSERT ===
for work_folder in os.listdir(BASE_DIR):
    work_path = os.path.join(BASE_DIR, work_folder)
    if not os.path.isdir(work_path):
        continue

    instrument_name = infer_instrument_from_folder(work_folder)
    instrument_id = get_instrument_id(instrument_name)

    # --- Extract BWV, title, key (hyphen-safe) ---
    m = re.match(r"(.+?)\s+BWV(\d+)", work_folder)
    if m:
        title_part, bwv_num = m.groups()
        bwv = f"BWV{bwv_num}"

        # key regex allows hyphen (E-flat, D#-minor)
        km = re.search(r"in\s+([A-G][#b]?(?:-?[a-z]+)?\s*(?:major|minor))", title_part, flags=re.I)
        key = km.group(1) if km else None

        # remove the "in <key>" part from title
        title = re.sub(r"\s+in\s+[A-G][#b]?(?:-?[a-z]+)?\s*(?:major|minor)", "", title_part, flags=re.I).strip()
    else:
        bwv = None
        title = work_folder
        key = None

    cur.execute("""
        INSERT INTO works (instrument_id,bwv,title,key,folder_path)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING work_id;
    """, (instrument_id, bwv, title, key, work_path))
    work_id = cur.fetchone()[0]

    print(f"Processing work: {title} (instrument -> {instrument_name}, key -> {key})")

    # Changed: Look for XML files instead of MIDI files
    xml_files = [f for f in os.listdir(work_path) if f.lower().endswith((".xml", ".musicxml", ".mxl"))]
    xml_files.sort()
    for idx, xml in enumerate(xml_files, start=1):
        movement_name = os.path.splitext(xml)[0]
        xml_path = os.path.join(work_path, xml)
        cur.execute("""
            INSERT INTO movements (work_id,movement_number,movement_name,xml_file_path)
            VALUES (%s,%s,%s,%s)
        """, (work_id, idx, movement_name, xml_path))

    print(f"  - inserted {len(xml_files)} movements for work_id={work_id}")