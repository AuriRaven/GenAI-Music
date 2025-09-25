import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from zipfile import ZipFile
from io import BytesIO

BASE_URL = "http://www.jsbach.net/midi/"
DEST_FOLDER = "bach_midis_by_BWV"
os.makedirs(DEST_FOLDER, exist_ok=True)

resp = requests.get(BASE_URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, 'html.parser')

subpages = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if href.startswith('midi_') and href.endswith('.html'):
        subpages.append(urljoin(BASE_URL, href))

print("Encontradas subpáginas:", subpages)

def find_bwv(text):
    """
    Return normalized BWV number from filename or None.
    Matches things like BWV1007, bwv 1007, 1007a, etc.
    Normalizes BWV1007a and BWV1007b to BWV1007.
    """
    if not text:
        return None
    m = re.search(r'(BWV)?\s*([0-9]{3,4})([a-zA-Z]?)', text, re.IGNORECASE)
    if m:
        num = m.group(2)  # digits only
        return f"BWV{num}"  # ignore trailing letter
    return None

for page in subpages:
    resp2 = requests.get(page)
    resp2.raise_for_status()
    soup2 = BeautifulSoup(resp2.text, 'html.parser')

    for link2 in soup2.find_all('a', href=True):
        href2 = link2['href'].strip()
        lower = href2.lower()

        # Case 1: individual MIDI file
        if lower.endswith('.mid'):
            midi_url = urljoin(page, href2)
            filename = os.path.basename(href2).replace(' ', '_')
            bwv = find_bwv(filename)
            if not bwv:
                bwv = "Misc"
            bwv_folder = os.path.join(DEST_FOLDER, bwv)
            os.makedirs(bwv_folder, exist_ok=True)
            dest_path = os.path.join(bwv_folder, filename)

            if not os.path.exists(dest_path):
                print(f"Descargando MIDI: {midi_url} → {bwv_folder}")
                r = requests.get(midi_url)
                if r.status_code == 200:
                    with open(dest_path, 'wb') as f:
                        f.write(r.content)

        # Case 2: zip file containing midis
        elif lower.endswith('.zip'):
            zip_url = urljoin(page, href2)
            zip_name = os.path.basename(href2).replace(' ', '_')
            bwv_from_zip = find_bwv(zip_name)  # BWV from zip name
            if not bwv_from_zip:
                bwv_from_zip = "Misc"
            print(f"Descargando ZIP: {zip_url} → {bwv_from_zip}")
            r = requests.get(zip_url)
            if r.status_code == 200:
                with ZipFile(BytesIO(r.content)) as zf:
                    for member in zf.namelist():
                        if member.lower().endswith('.mid'):
                            midi_name = os.path.basename(member).replace(' ', '_')
                            # prefer BWV from midi file name; else from zip
                            bwv = find_bwv(midi_name) or bwv_from_zip
                            bwv_folder = os.path.join(DEST_FOLDER, bwv)
                            os.makedirs(bwv_folder, exist_ok=True)
                            dest_file = os.path.join(bwv_folder, midi_name)
                            if not os.path.exists(dest_file):
                                with zf.open(member) as source, open(dest_file, 'wb') as target:
                                    target.write(source.read())
                                print(f"Extraído {midi_name} en {bwv_folder}")
