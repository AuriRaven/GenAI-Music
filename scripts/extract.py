import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Optional, Tuple
import tempfile

# Import music21 for MIDI to MusicXML conversion
try:
    from music21 import converter
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("WARNING: music21 not installed. Install it with: pip install music21")

BASE_URL: str = "http://www.jsbach.net/midi/"
DEST_ROOT: str = "data"  # Data directory in current path

# Target instruments
TARGET_INSTRUMENTS: Dict[str, str] = {
    "midi_solo_cello.html": "Cello",
    "midi_solo_violin.html": "Violin", 
    "midi_solo_flute.html": "Flute"
}

# Known BWV mappings for common filename patterns
BWV_MAPPINGS: Dict[str, Tuple[str, str]] = {
    # Cello Suites
    'cs1': ('BWV1007', 'Suite No. 1 in G major'),
    'cs2': ('BWV1008', 'Suite No. 2 in D minor'),
    'cs3': ('BWV1009', 'Suite No. 3 in C major'),
    'cs4': ('BWV1010', 'Suite No. 4 in E-flat major'),
    'cs5': ('BWV1011', 'Suite No. 5 in C minor'),
    'cs6': ('BWV1012', 'Suite No. 6 in D major'),
    # Violin Sonatas and Partitas
    'vs1': ('BWV1001', 'Sonata No. 1 in G minor'),
    'vp1': ('BWV1002', 'Partita No. 1 in B minor'),
    'vs2': ('BWV1003', 'Sonata No. 2 in A minor'),
    'vp2': ('BWV1004', 'Partita No. 2 in D minor'),
    'vs3': ('BWV1005', 'Sonata No. 3 in C major'),
    'vp3': ('BWV1006', 'Partita No. 3 in E major'),
    # Flute Partita
    'fp': ('BWV1013', 'Partita in A minor'),
}


def clean_name(text: str) -> str:
    """
    Make a filesystem-friendly name by removing invalid characters.
    
    Args:
        text: The text string to clean
        
    Returns:
        A cleaned string safe for use in filesystem paths
        
    Example:
        >>> clean_name("Suite No. 1 / BWV 1007")
        'Suite No. 1  BWV 1007'
        >>> clean_name("Menuet I/II")
        'Menuet I_II'
    """
    # Replace forward slashes with underscores
    text = text.replace('/', '_')
    # Remove other invalid filesystem characters
    return re.sub(r'[^A-Za-z0-9_\-#. ]+', '', text).strip()


def extract_bwv_from_filename(filename: str) -> Optional[Tuple[str, str]]:
    """
    Extract BWV number and work title from filename using known patterns.
    
    Args:
        filename: MIDI filename to analyze
        
    Returns:
        Tuple of (BWV number, work title) or None if not found
        
    Example:
        >>> extract_bwv_from_filename("cs1-1pre.mid")
        ('BWV1007', 'Suite No. 1 in G major')
    """
    # Try to match known patterns (cs1, vs2, vp3, fp, etc.)
    for pattern, (bwv, title) in BWV_MAPPINGS.items():
        if filename.lower().startswith(pattern):
            return (bwv, title)
    return None


def extract_bwv(text: str) -> Optional[str]:
    """
    Extract BWV (Bach-Werke-Verzeichnis) catalog number from text.
    
    Args:
        text: Text string that may contain a BWV number
        
    Returns:
        Formatted BWV string (e.g., "BWV1004") or None if not found
        
    Example:
        >>> extract_bwv("Partita No. 2 BWV 1004")
        'BWV1004'
        >>> extract_bwv("Some random text")
        None
    """
    match = re.search(r'BWV\s*(\d{3,4}[a-zA-Z]?)', text, re.IGNORECASE)
    if match:
        return f"BWV{match.group(1)}"
    return None


def extract_work_title(text: str) -> Optional[str]:
    """
    Extract the main work title from text (portion before BWV number).
    
    Args:
        text: Text string containing work information
        
    Returns:
        Cleaned work title or None if BWV pattern not found
        
    Example:
        >>> extract_work_title("Partita No. 2 in D minor BWV1004")
        'Partita No. 2 in D minor'
    """
    # Try to get text before BWV
    bwv_match = re.search(r'(.+?)\s*BWV', text, re.IGNORECASE)
    if bwv_match:
        title = bwv_match.group(1).strip()
        # Clean up common prefixes for consistent formatting
        title = re.sub(r'^(Suite|Partita|Sonata)\s+', r'\1 ', title, flags=re.IGNORECASE)
        return clean_name(title)
    return None


def extract_movement_info(filename: str) -> str:
    """
    Extract movement number and name from MIDI filename.
    
    Attempts to parse various filename formats to create a standardized
    movement name in the format "N Movement_Name" where N is the movement number.
    
    Args:
        filename: The MIDI filename (with or without .mid extension)
        
    Returns:
        Formatted movement string (e.g., "1 Allemande", "3 Sarabande")
        
    Example:
        >>> extract_movement_info("cs1-1pre.mid")
        '1 Prelude'
        >>> extract_movement_info("vp2-3sar.mid")
        '3 Sarabande'
    """
    # Remove .mid extension
    name = filename.replace('.mid', '').replace('.MID', '')
    
    # Movement name mappings for common abbreviations
    movement_names: Dict[str, str] = {
        'pre': 'Prelude',
        'all': 'Allemande',
        'ald': 'Allemande (Double)',
        'cou': 'Courante',
        'cod': 'Courante (Double)',
        'sar': 'Sarabande',
        'sad': 'Sarabande (Double)',
        'men': 'Menuet',
        'min': 'Menuet',
        'bou': 'Bourrée',
        'gig': 'Gigue',
        'gav': 'Gavotte',
        'fug': 'Fugue',
        'ada': 'Adagio',
        'and': 'Andante',
        'alg': 'Allegro',
        'prs': 'Presto',
        'sic': 'Siciliana',
        'cha': 'Chaconne',
        'gra': 'Grave',
        'lar': 'Largo',
        'lou': 'Loure',
        'tb': 'Tempo di Borea',
        'tbd': 'Tempo di Borea (Double)',
        'al': 'Allemande',
        'co': 'Courante',
        'sa': 'Sarabande',
    }
    
    # Pattern for files like "cs1-1pre", "vp2-3sar", "fp-2cou"
    # Format: [prefix][number]-[movement_number][movement_abbrev]
    match = re.search(r'[a-z]+\d*-(\d+)([a-z]+)', name.lower())
    if match:
        movement_num = match.group(1)
        movement_abbrev = match.group(2)
        
        # Look up the full movement name
        if movement_abbrev in movement_names:
            return f"{movement_num} {movement_names[movement_abbrev]}"
        else:
            # If not found, capitalize the abbreviation
            return f"{movement_num} {movement_abbrev.capitalize()}"
    
    # Try to find pattern like "01_allemande" or "1-allemande" or "1 Allemande"
    match = re.search(r'^(\d+)[\s\-_]+(.+)', name)
    if match:
        num = match.group(1).lstrip('0') or '0'
        movement = match.group(2).replace('_', ' ').replace('-', ' ').strip().title()
        return f"{num} {movement}"
    
    # Fallback: try to extract just the movement number and abbreviation
    match = re.search(r'(\d+)([a-z]+)', name.lower())
    if match:
        num = match.group(1)
        abbrev = match.group(2)
        if abbrev in movement_names:
            return f"{num} {movement_names[abbrev]}"
    
    # Last resort: use the filename as-is with cleaned formatting
    return name.replace('_', ' ').replace('-', ' ').strip().title()


def convert_midi_to_musicxml(midi_data: bytes, output_path: str) -> bool:
    """
    Convert MIDI data to MusicXML format using music21.
    
    Args:
        midi_data: The raw MIDI file data as bytes
        output_path: The path where the MusicXML file should be saved
        
    Returns:
        True if conversion was successful, False otherwise
    """
    if not MUSIC21_AVAILABLE:
        print("      ✗ music21 library not available for conversion")
        return False
    
    try:
        # Write MIDI data to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_midi:
            temp_midi.write(midi_data)
            temp_midi_path = temp_midi.name
        
        # Parse the MIDI file
        score = converter.parse(temp_midi_path)
        
        # Write as MusicXML
        score.write('musicxml', fp=output_path)
        
        # Clean up temporary file
        os.unlink(temp_midi_path)
        
        return True
        
    except Exception as e:
        print(f"      ✗ Error converting MIDI to MusicXML: {e}")
        # Clean up temp file if it exists
        try:
            if 'temp_midi_path' in locals():
                os.unlink(temp_midi_path)
        except:
            pass
        return False


def download_and_convert_to_xml(url: str, dest_path: str, timeout: int = 10) -> bool:
    """
    Download a MIDI file from a URL, convert it to MusicXML, and save it.
    
    Args:
        url: The URL of the MIDI file to download
        dest_path: The local filesystem path where the XML file should be saved
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        True if download and conversion were successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Convert MIDI data to MusicXML
        return convert_midi_to_musicxml(response.content, dest_path)
        
    except requests.RequestException as e:
        print(f"      ✗ Error downloading from {url}: {e}")
        return False


def extract_movement_from_table_row(link) -> Optional[Tuple[str, str]]:
    """
    Extract movement number and name from the HTML table structure.
    
    The structure is typically:
    <TR>
        <TD>1.</TD>
        <TD>Prelude</TD>
        <TD><A HREF="cs1-1pre.mid">cs1-1pre.mid</A></TD>
    </TR>
    
    Args:
        link: BeautifulSoup link element containing the MIDI file
        
    Returns:
        Tuple of (movement_number, movement_name) or None if not found
    """
    # Find the parent TR (table row)
    tr = link.find_parent('tr')
    if not tr:
        return None
    
    # Get all TD cells in this row
    tds = tr.find_all('td')
    if len(tds) < 2:
        return None
    
    # First TD usually contains the movement number
    movement_num_text = tds[0].get_text(strip=True)
    # Remove trailing period if present
    movement_num = movement_num_text.rstrip('.')
    
    # Second TD usually contains the movement name
    movement_name = tds[1].get_text(strip=True)
    
    # Clean up the movement name
    movement_name = movement_name.strip()
    
    if movement_num and movement_name:
        return (movement_num, movement_name)
    
    return None


def parse_midi_links(soup: BeautifulSoup, page_url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse a BeautifulSoup object to extract MIDI file links grouped by work.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML page
        page_url: The URL of the page being parsed (for constructing absolute URLs)
        
    Returns:
        Dictionary mapping work keys (e.g., "Partita No. 2 BWV1004") to lists
        of file information dictionaries containing 'url', 'filename', 'bwv', and 'movement_info'
    """
    works: Dict[str, List[Dict[str, str]]] = {}
    
    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        
        # Only process direct .mid files (ignore .zip as requested)
        if not href.lower().endswith('.mid'):
            continue
        
        midi_url = urljoin(page_url, href)
        filename = os.path.basename(href)
        
        # Try to extract movement info from the HTML table structure
        movement_info = extract_movement_from_table_row(link)
        
        # Get link text which often contains work info
        link_text = link.get_text(strip=True)
        
        # Try to find parent element text for more context
        parent_text = ""
        if link.parent:
            parent_text = link.parent.get_text(strip=True)
        
        combined_text = f"{parent_text} {link_text} {filename}"
        
        # First try to extract BWV from the combined text
        bwv = extract_bwv(combined_text)
        work_title = None
        
        # If not found, try the filename pattern matching
        if not bwv:
            result = extract_bwv_from_filename(filename)
            if result:
                bwv, work_title = result
            else:
                print(f"⚠ Skipping {filename} - no BWV found")
                continue
        
        # Extract work title if we don't have it yet
        if not work_title:
            work_title = extract_work_title(combined_text)
            if not work_title:
                work_title = f"Work {bwv}"
        
        # Create unique key for this work
        work_key = f"{work_title} {bwv}"
        
        if work_key not in works:
            works[work_key] = []
        
        works[work_key].append({
            'url': midi_url,
            'filename': filename,
            'bwv': bwv,
            'movement_info': movement_info
        })
    
    return works


def process_instrument_page(page_url: str, instrument: str, dest_root: str) -> None:
    """
    Process a single instrument's MIDI page, downloading and converting all files to MusicXML.
    
    Downloads all MIDI files for works by the specified instrument, converts them to MusicXML,
    and organizes them into a directory structure: data/Work_Title_BWV####/movement_files.xml
    
    Args:
        page_url: The URL of the instrument's MIDI page
        instrument: Name of the instrument (e.g., "Cello", "Violin")
        dest_root: Root directory where files should be saved
        
    Returns:
        None
    """
    if not MUSIC21_AVAILABLE:
        print("\n⚠ ERROR: music21 library is required for MIDI to MusicXML conversion")
        print("Install it with: pip install music21")
        return
    
    print(f"\n{'='*60}")
    print(f"Processing {instrument} solos from {page_url}")
    print(f"{'='*60}")
    
    try:
        resp = requests.get(page_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error accessing {page_url}: {e}")
        return
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    works = parse_midi_links(soup, page_url)
    
    # Download and organize files
    for work_key, files in works.items():
        if not files:
            continue
        
        # Create directory structure: data/Work_Title_BWV1004/
        work_dir = os.path.join(dest_root, work_key)
        os.makedirs(work_dir, exist_ok=True)
        
        print(f"\n📁 {work_key}")
        
        for file_info in files:
            midi_url = file_info['url']
            original_filename = file_info['filename']
            
            # Generate movement-based filename
            # First try to use the movement info from HTML structure
            if file_info.get('movement_info'):
                movement_num, movement_name = file_info['movement_info']
                # Clean the movement name to remove problematic characters
                movement_name = clean_name(movement_name)
                new_filename = f"{movement_num} {movement_name}"
            else:
                # Fallback to extracting from filename
                new_filename = extract_movement_info(original_filename)
                new_filename = clean_name(new_filename)
            
            # Change extension to .xml (or .musicxml)
            if new_filename.lower().endswith('.mid'):
                new_filename = new_filename[:-4] + '.xml'
            elif not new_filename.lower().endswith('.xml'):
                new_filename += '.xml'
            
            dest_path = os.path.join(work_dir, new_filename)
            
            # Skip if already exists
            if os.path.exists(dest_path):
                print(f"   ✓ {new_filename} (already exists)")
                continue
            
            # Download and convert the MIDI file to MusicXML
            print(f"   ⬇ Downloading and converting: {new_filename}")
            success = download_and_convert_to_xml(midi_url, dest_path)
            
            if success:
                print(f"   ✓ Saved: {new_filename}")