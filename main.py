from scripts.extract import process_instrument_page
import os
from urllib.parse import urljoin
from typing import Dict

BASE_URL: str = "http://www.jsbach.net/midi/"
DEST_ROOT: str = "data"  # Data directory in current path

# Target instruments
TARGET_INSTRUMENTS: Dict[str, str] = {
    "midi_solo_cello.html": "Cello",
    "midi_solo_violin.html": "Violin", 
    "midi_solo_flute.html": "Flute"
}

def main() -> None:
    """
    Main entry point for the Bach solo works MIDI extractor.
    
    Downloads and organizes MIDI files for Bach's solo works for cello, violin,
    and flute from jsbach.net, creating a structured directory hierarchy within
    a 'data' folder in the current directory.
    """
    # Create the data directory if it doesn't exist
    os.makedirs(DEST_ROOT, exist_ok=True)
    print(f"📂 Using data directory: {os.path.abspath(DEST_ROOT)}")
    
    # Process each target instrument
    for page_file, instrument in TARGET_INSTRUMENTS.items():
        page_url = urljoin(BASE_URL, page_file)
        process_instrument_page(page_url, instrument, DEST_ROOT)
    
    print(f"\n{'='*60}")
    print("✅ Download complete!")
    print(f"📂 All files saved to: {os.path.abspath(DEST_ROOT)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()