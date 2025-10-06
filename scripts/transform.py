import os
import pandas as pd
from music21 import converter, note, chord, key

def extract_features_from_chord(ch, current_key):
    """
    Extracts a feature dictionary from a chord.
    """
    pitches = [p for p in ch.pitches]
    pitch_classes = [p.pitchClass for p in pitches]
    duration = ch.quarterLength
    beat = ch.beat
    measure_num = ch.measureNumber

    # Weighted pitch class histogram (duration as weight)
    pc_hist = {f"pc_{i}": 0 for i in range(12)}
    for p in pitches:
        pc_hist[f"pc_{p.pitchClass}"] += duration

    # Root note and bass note
    root = ch.root().name if ch.isChord else None
    bass = pitches[0].name if pitches else None

    # Current key context
    local_key = current_key.tonic.name if current_key else None
    mode = current_key.mode if current_key else None

    return {
        "measure": measure_num,
        "beat": beat,
        "duration": duration,
        "num_notes": len(pitches),
        "root": root,
        "bass": bass,
        "local_key": local_key,
        "mode": mode,
        **pc_hist,
        "chord_name": ch.pitchedCommonName
    }

def process_xml_file(filepath):
    """
    Processes a single accompaniment XML file and returns a DataFrame of features.
    """
    score = converter.parse(filepath)

    # Get accompaniment staff (second part if exists, else first)
    if len(score.parts) > 1:
        accomp = score.parts[1]
    else:
        accomp = score.parts[0]

    # Try to get the global key signature (whole score context)
    try:
        current_key = score.analyze('key')
    except Exception:
        current_key = None

    # Extract chords from accompaniment
    accomp_chords = accomp.chordify()

    rows = []
    for elem in accomp_chords.recurse().getElementsByClass(chord.Chord):
        feat = extract_features_from_chord(elem, current_key)
        rows.append(feat)

    return pd.DataFrame(rows)

def process_all_accomp_files(dest_root="./data", concat=False):
    """
    Walks through DEST_ROOT, processes all '*Accomp.xml' files,
    and returns either:
      - a dict {filepath: dataframe} if concat=False
      - a single concatenated DataFrame with 'piece_name' if concat=True
    """
    results = {}
    all_dfs = []

    for root, dirs, files in os.walk(dest_root):
        for f in files:
            if f.endswith("Accomp.xml"):
                filepath = os.path.join(root, f)
                try:
                    df = process_xml_file(filepath)
                    df["piece_name"] = os.path.basename(root)  # folder name as piece
                    results[filepath] = df
                    all_dfs.append(df)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    if concat:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return results
