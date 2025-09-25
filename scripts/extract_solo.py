import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from zipfile import ZipFile
from io import BytesIO

BASE_URL = "http://www.jsbach.net/midi/"
DEST_ROOT = "bach_midis_solo_all"
os.makedirs(DEST_ROOT, exist_ok=True)

def clean_name(text):
    """Make a filesystem-friendly name."""
    return re.sub(r'[^A-Za-z0-9_\- ]+', '', text).strip().replace(' ', '_')

def find_bwv(text):
    """Extract BWV number (ignoring trailing letters) if present."""
    m = re.search(r'(BWV)?\s*([0-9]{3,4})([a-zA-Z]?)', text, re.IGNORECASE)
    if m:
        return f"BWV{m.group(2)}"
    return None

# --- Step 1: find all “solo” subpages ---
resp = requests.get(BASE_URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, 'html.parser')

solo_pages = {}
for link in soup.find_all('a', href=True):
    href = link['href']
    # if it’s a midi_*.html and “solo” is in the name
    if href.startswith("midi_solo_") and href.endswith(".html"):
        page_url = urljoin(BASE_URL, href)
        # instrument name from link text (or from filename)
        inst = link.get_text(strip=True)
        if not inst:
            # fallback: derive from the href, e.g. midi_solo_violin → Violin
            inst = href[len("midi_solo_"):-len(".html")]
        solo_pages[page_url] = inst

print("Solo instrument MIDI pages found:", solo_pages)

# --- Step 2: download & organize from each solo page ---
for page_url, instrument in solo_pages.items():
    print(f"\n=== Processing instrument: {instrument} from {page_url} ===")
    resp2 = requests.get(page_url)
    resp2.raise_for_status()
    soup2 = BeautifulSoup(resp2.text, 'html.parser')
    
    for link2 in soup2.find_all('a', href=True):
        href2 = link2['href'].strip()
        lower = href2.lower()

        # Case A: direct .mid file
        if lower.endswith('.mid'):
            midi_url = urljoin(page_url, href2)
            filename = os.path.basename(href2).replace(' ', '_')
            bwv = find_bwv(filename) or "Misc"
            target_dir = os.path.join(DEST_ROOT, instrument, bwv)
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, filename)
            if not os.path.exists(dest_path):
                print("Downloading", midi_url, "->", dest_path)
                r = requests.get(midi_url)
                if r.status_code == 200:
                    with open(dest_path, 'wb') as f:
                        f.write(r.content)

        # Case B: ZIP containing .mid files
        elif lower.endswith('.zip'):
            zip_url = urljoin(page_url, href2)
            zip_name = os.path.basename(href2).replace(' ', '_')
            bwv_from_zip = find_bwv(zip_name) or "Misc"
            print("Downloading ZIP:", zip_url)
            r = requests.get(zip_url)
            if r.status_code == 200:
                with ZipFile(BytesIO(r.content)) as zf:
                    for member in zf.namelist():
                        if member.lower().endswith('.mid'):
                            midi_name = os.path.basename(member).replace(' ', '_')
                            bwv = find_bwv(midi_name) or bwv_from_zip
                            target_dir = os.path.join(DEST_ROOT, instrument, bwv)
                            os.makedirs(target_dir, exist_ok=True)
                            dest_file = os.path.join(target_dir, midi_name)
                            if not os.path.exists(dest_file):
                                with zf.open(member) as source, open(dest_file, 'wb') as target:
                                    target.write(source.read())
                                print("Extracted", midi_name, "->", dest_file)
