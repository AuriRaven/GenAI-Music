from scripts.extract import process_instrument_page
from scripts.load import conn, cur
from scripts.accomp import add_accompaniment_to_all_xml
from scripts.musicxml import open_in_musescore
from scripts.transform import process_all_accomp_files
from scripts.random_forest import train_random_forest
from scripts.neural_network import train_nn
import os
from urllib.parse import urljoin
from typing import Dict

BASE_URL: str = "http://www.jsbach.net/midi/"
DEST_ROOT: str = "data"  # Data directory in current path
xml_files = [
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data\Suite No. 1 in G major BWV1007\1 Prelude Accomp Accomp.xml",
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data\Suite No. 5 in C minor BWV1011\1 Prelude Accomp Accomp.xml",
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data\Partita in A minor BWV1013\1 Allemande Accomp Accomp.xml",
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data\Partita No. 3 in E major BWV1006\3 Gavotte en Rondeau Accomp Accomp.xml"
    ]

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

    # Add piano accompaniment to all MusicXML files
    #add_accompaniment_to_all_xml(DEST_ROOT)

    # Transform Accompaniment XML files into DataFrames for training set
    df = process_all_accomp_files("./data", concat=True)
    print("=== Sample of Training Space ===")
    print(df.head())
    print(df["piece_name"].unique())
    df.to_csv("./data/training_space.csv", index=False)

    # Train Random Forest
    model, metrics = train_random_forest(df, target_col="chord_name")

    # Print metrics for Random Forest
    print("=== TRAINING METRICS ===")
    print(f"Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Precision: {metrics['train_precision']:.4f}")
    print(f"Recall: {metrics['train_recall']:.4f}")
    print(f"F1-score: {metrics['train_f1']:.4f}")

    print("\n=== VALIDATION METRICS ===")
    print(f"Accuracy: {metrics['val_accuracy']:.4f}")
    print(f"Precision: {metrics['val_precision']:.4f}")
    print(f"Recall: {metrics['val_recall']:.4f}")
    print(f"F1-score: {metrics['val_f1']:.4f}")

    print("\n=== CLASSIFICATION REPORT ===")
    print(metrics['classification_report'])

    # Train Neural Network
    model, metrics, encoder = train_nn(df, target_col="chord_name", prev_chords=True, epochs=50)

    # Print metrics for Neural Network
    print("=== TRAINING RESULTS ===")
    print(f"Train Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Validation Accuracy: {metrics['val_accuracy']:.4f}")

    # Load the database with the downloaded files
    conn.commit()
    cur.close()
    conn.close()
    print("Database filled successfully ✅")

    for xml_file in xml_files:
        print(f"Opening {xml_file} in MuseScore...")
        open_in_musescore(xml_file)
    print("✅ XML files Opened in MuseScore!")
    print("All done! 🎵")

if __name__ == "__main__":
    main()