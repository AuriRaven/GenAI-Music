import os
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm
from music21 import converter, note, chord, stream, interval, analysis

DATA_PATH = Path(r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\data")
OUT_CSV = Path(r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\raw_data\measure_features_raw.csv")

def rhythmic_entropy(durations):
    if len(durations) == 0:
        return 0.0
    vals, counts = np.unique(durations, return_counts=True)
    probs = counts / counts.sum()
    return float(-(probs * np.log2(probs)).sum())

def pc_vector_from_notes(notes):
    pcs = [n.pitch.pitchClass for n in notes if isinstance(n, note.Note)]
    vec = np.zeros(12, dtype=int)
    for p in pcs:
        vec[p] += 1
    return vec

def detect_chords_in_measure(meas):
    # devuelve lista de music21.chord.Chord en la medida (si hay)
    return [el for el in meas.recurse().getElementsByClass(chord.Chord)]

def root_and_type_from_chord(c):
    try:
        root_pc = c.root().pitchClass
        # tipo simplificado
        if c.isTriad():
            if c.commonName and 'major' in c.commonName.lower():
                t = 'maj'
            elif c.commonName and 'minor' in c.commonName.lower():
                t = 'min'
            else:
                t = 'triad'
        elif any(p.name == '7' for p in c.pitches):
            t = '7'
        else:
            t = 'other'
        return root_pc, t
    except Exception:
        return None, None

def degree_and_function(root_pc, key_obj):
    # key_obj: music21.key.Key
    if key_obj is None or root_pc is None:
        return np.nan, 'None'
    tonic_pc = key_obj.tonic.pitchClass
    degree = (root_pc - tonic_pc) % 12
    # map semitone offset to scale degree index (C major: 0->I,2->II,...)
    # aproximación: busca grado más cercano en escala del key
    scale_pcs = [p.pitchClass for p in key_obj.getScale().getPitches()]
    if degree in scale_pcs:
        deg_idx = scale_pcs.index(degree)  # 0..len(scale)-1
        # map to classical roman degrees: 0->I,1->II...
        # function heuristic:
        if deg_idx in (0, 5):  # I or vi in major (vi often tonic-related)
            func = 'T'
        elif deg_idx in (3, 1):  # IV or ii
            func = 'S'
        elif deg_idx in (4, 6):  # V or vii°
            func = 'D'
        else:
            func = 'O'
        return deg_idx + 1, func
    else:
        # if not in scale, fallback: compute closest pitch class mapping
        # mark as Other
        return np.nan, 'O'

rows = []
for root, dirs, files in os.walk(DATA_PATH):
    for fname in files:
        if fname.lower().endswith("accomp.xml") or "accomp" in fname.lower():
            fullpath = Path(root) / fname
            # metadata from path
            # asumimos estructura: .../Suite Name/<movement files>
            parts = Path(root).parts
            suite = parts[-2] if len(parts) >= 2 else parts[-1]
            movement = fname.replace('.xml','')
            try:
                score = converter.parse(str(fullpath))
            except Exception as e:
                print("Error parsing:", fullpath, e)
                continue

            # intentar detectar key por movimiento (music21)
            try:
                key_obj = score.analyze('key')
                key_name = key_obj.tonic.name
                mode = key_obj.mode
            except Exception:
                key_obj = None
                key_name = None
                mode = None

            # localizar partes: preferir la parte que contiene acordes (accompaniment)
            parts_list = score.parts
            # heurística: elegir la parte con más acordes
            max_chords = -1
            accomp_part = None
            melody_part = None
            for p in parts_list:
                n_ch = len([c for c in p.recurse().getElementsByClass(chord.Chord)])
                if n_ch > max_chords:
                    max_chords = n_ch
                    accomp_part = p
            # melody as the part with most notes but few chords (heurística)
            max_notes = -1
            for p in parts_list:
                n_notes = len([n for n in p.recurse().notes])
                if n_notes > max_notes:
                    max_notes = n_notes
                    melody_part = p

            # if parts are not well separated, fallback to score.recurse()
            measure_stream = None
            if melody_part is not None:
                measure_stream = melody_part.measures(0, None)
            else:
                measure_stream = score.parts[0].measures(0, None)

            # iterate measures using accompaniment part measures to align harmony
            acc_measures = accomp_part.getElementsByClass(stream.Measure)
            for meas in acc_measures:
                mi = meas.measureNumber
                # get corresponding melody notes within same measure number (if melody_part exists)
                if melody_part:
                    try:
                        melody_meas = melody_part.measure(mi)
                        melody_notes = [n for n in melody_meas.notes] if melody_meas else []
                    except Exception:
                        melody_notes = []
                else:
                    melody_notes = [n for n in score.recurse().notes if n.measureNumber == mi]

                # harmonic chords in this measure (from accompaniment)
                chords_in_m = detect_chords_in_measure(meas)
                # aggregate chord info
                chord_roots = []
                chord_types = []
                for c in chords_in_m:
                    r,t = root_and_type_from_chord(c)
                    if r is not None:
                        chord_roots.append(r)
                        chord_types.append(t)

                # melodic pitches in measure (melody voice)
                melody_pitches = [n.pitch.midi for n in melody_notes if isinstance(n, note.Note)]
                # durations of notes in measure (melody)
                durations = [n.quarterLength for n in melody_notes if isinstance(n, note.Note)]

                # pitch class vector from melody + accompaniment (todo: decide si incluir both)
                pc_vec = pc_vector_from_notes([n for n in meas.recurse().notes if isinstance(n, note.Note)])
                pc_vec_norm = pc_vec / (pc_vec.sum() if pc_vec.sum() > 0 else 1)

                melodic_range = int(max(melody_pitches)-min(melody_pitches)) if len(melody_pitches) >= 2 else 0
                mean_interval = float(np.mean([abs(int(melody_pitches[i+1]-melody_pitches[i])) 
                                               for i in range(len(melody_pitches)-1)]) ) if len(melody_pitches) >= 2 else 0.0
                large_jump_pct = float(sum(1 for i in range(len(melody_pitches)-1) if abs(melody_pitches[i+1]-melody_pitches[i])>4) / max(1, (len(melody_pitches)-1)))

                note_density = len(melody_pitches)  # notas melódicas por compás
                avg_duration = float(np.mean(durations)) if durations else 0.0
                r_ent = rhythmic_entropy(durations) if durations else 0.0
                most_common_duration = max(set(durations), key=durations.count) if durations else 0.0

                # harmonic derived
                num_distinct_chords = len(set(tuple(c.normalOrder) for c in chords_in_m)) if chords_in_m else 0
                most_common_root = int(chord_roots[0]) if chord_roots else np.nan
                most_common_type = chord_types[0] if chord_types else None

                # degree and function relative to key (use most_common_root)
                degree, func = degree_and_function(most_common_root, key_obj) if most_common_root is not np.nan else (np.nan, 'O')

                row = {
                    "suite": suite,
                    "movement": movement,
                    "file": str(fullpath),
                    "measure_index": int(mi),
                    "key_local": key_name,
                    "mode_local": mode,
                    "measure_length_quarter": float(meas.barDuration.quarterLength) if hasattr(meas, 'barDuration') and meas.barDuration is not None else np.nan,
                    "num_distinct_chords": num_distinct_chords,
                    "most_common_chord_root": most_common_root,
                    "most_common_chord_type": most_common_type,
                    "degree_relative_to_key": degree,
                    "function": func,
                    "melodic_range": melodic_range,
                    "mean_interval": mean_interval,
                    "large_jump_pct": large_jump_pct,
                    "num_notes_melody": int(note_density),
                    "avg_duration": avg_duration,
                    "rhythmic_entropy": r_ent,
                    "most_common_duration": most_common_duration,
                    "note_density": note_density
                }
                # attach pc_vector columns
                for i in range(12):
                    row[f"pc_{i}"] = int(pc_vec[i])

                rows.append(row)

# dataframe and save
df = pd.DataFrame(rows)
df.to_csv(OUT_CSV, index=False)
print("✔ Guardado:", OUT_CSV)
