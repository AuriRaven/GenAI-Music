# accompaniment.py

import os
from music21 import converter, note, chord, stream, instrument, key, tempo, metadata

# ----------------------
# Harmony Utilities
# ----------------------
def get_key_harmony_named(music_key):
    """Return a dictionary mapping scale degrees to triads in the given key."""
    degree_names_major = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    degree_names_minor = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
    degree_names = degree_names_major if music_key.mode == 'major' else degree_names_minor
    scale_pitches = music_key.getScale().getPitches()
    harmony = {}
    for i, name in enumerate(degree_names):
        root = scale_pitches[i]
        third = scale_pitches[(i + 2) % 7]
        fifth = scale_pitches[(i + 4) % 7]
        harmony[name] = chord.Chord([root, third, fifth])
    return harmony


def chord_distance_no_octave(chord_candidate, note_group):
    """Compute distance between chord and notes ignoring octaves."""
    chord_set = set(p.name for p in chord_candidate.pitches)
    input_set = set(n.name for n in note_group if isinstance(n, note.Note))
    return len(chord_set.symmetric_difference(input_set))


def get_common_modulation_keys(music_key):
    """Return the most common related keys for modulation detection."""
    tonic = music_key.tonic
    fifth_up = key.Key(tonic.transpose(7))
    fifth_down = key.Key(tonic.transpose(-7))
    relative = music_key.relative
    return [music_key, fifth_up, fifth_down, relative]


def detect_chord_with_modulation(note_group, base_key):
    """Detect the best matching chord in a group of notes, considering modulations."""
    candidate_keys = get_common_modulation_keys(base_key)
    best_match = None
    best_key = None
    best_degree = None
    min_distance = float('inf')

    for cand_key in candidate_keys:
        harmony = get_key_harmony_named(cand_key)
        for degree_name, chord_obj in harmony.items():
            dist = chord_distance_no_octave(chord_obj, note_group)
            if dist < min_distance:
                min_distance = dist
                best_match = chord_obj
                best_key = cand_key
                best_degree = degree_name

    return {
        "key": best_key,
        "chord": best_match,
        "degree": best_degree,
        "distance": min_distance
    }

# ----------------------
# Main Accompaniment Function
# ----------------------
def add_piano_accompaniment(midi_or_xml_path):
    """
    Given a MIDI or MusicXML file path, generates a piano accompaniment
    based on chord detection and saves MIDI and MusicXML in the same folder
    with ' Accomp' appended to the file name.
    """
    folder = os.path.dirname(midi_or_xml_path)
    base_name, ext = os.path.splitext(os.path.basename(midi_or_xml_path))
    output_title = f"{base_name} Accomp"

    # Load the file (works with MIDI or XML)
    score = converter.parse(midi_or_xml_path)
    part = score.parts[0]

    # Detect key
    base_key = part.analyze('key')

    # Prepare parts
    cello_part = stream.Part()
    cello_part.insert(0, instrument.Violoncello())
    for n in part.flat.notesAndRests:
        cello_part.append(n)

    piano_part = stream.Part()
    piano_part.insert(0, instrument.Piano())

    # Generate chords per measure
    for measure in part.getElementsByClass('Measure'):
        notes_in_measure = [n for n in measure.notes if isinstance(n, note.Note)]
        if len(notes_in_measure) >= 3:
            result = detect_chord_with_modulation(notes_in_measure, base_key)
            harmony_chord = result['chord']
            if harmony_chord:
                harmony_chord.duration = measure.duration
                harmony_chord.stemDirection = 'down'
                harmony_chord.addLyric(result['degree'])
                piano_part.append(harmony_chord)
        else:
            r = note.Rest()
            r.duration = measure.duration
            piano_part.append(r)

    # Combine into score
    full_score = stream.Score()
    full_score.insert(0, metadata.Metadata())
    full_score.metadata.title = f"{base_name} with Accompaniment"
    full_score.insert(0, tempo.MetronomeMark(number=60))
    full_score.append(cello_part)
    full_score.append(piano_part)

    # Save files in same folder with "Accomp" appended
    midi_file_path = os.path.join(folder, f"{output_title}.mid")
    xml_file_path = os.path.join(folder, f"{output_title}.xml")
    full_score.write('midi', fp=midi_file_path)
    full_score.write('musicxml', fp=xml_file_path)

    print(f"✅ Generated MIDI: {midi_file_path}")
    print(f"✅ Generated MusicXML: {xml_file_path}")

    return midi_file_path, xml_file_path

# ----------------------
# Batch Processing Function
# ----------------------
def add_accompaniment_to_all_xml(root_dir):
    """
    Recursively find all XML files in root_dir and generate accompaniment for each file.
    Saves output in the same folder with ' Accomp' appended.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                file_path = os.path.join(dirpath, filename)
                try:
                    add_piano_accompaniment(file_path)
                except Exception as e:
                    print(f"❌ Failed to process {file_path}: {e}")
