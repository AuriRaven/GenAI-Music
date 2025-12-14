"""
Stage C.1 – Harmonic Variable Normalization

This script normalizes harmonic-related variables in a
measure-level dataset derived from Bach solo string music.

Goals:
- Preserve musically meaningful zeros and NaNs
- Explicitly encode the presence of vertical harmony
- Stabilize functional harmony categories
- Clean chord-type representations

No imputation or row removal is performed.
"""

from pathlib import Path
import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

BASE_PATH = Path(r"C:\Users\Aura De La Garza G\Projects\GenAI-Music")

IN_CSV = (
    BASE_PATH
    / "unsupervised"
    / "curated_data"
    / "measure_features_identifiers.csv"
)

OUT_CSV = (
    BASE_PATH
    / "unsupervised"
    / "curated_data"
    / "measure_features_harmonic_normalized.csv"
)


# ---------------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------------

df = pd.read_csv(IN_CSV)


# ---------------------------------------------------------------------
# 1. Explicit harmony indicator
# ---------------------------------------------------------------------
# Measures with num_distinct_chords > 0 contain detectable
# vertical simultaneities (explicit harmony)

df["has_explicit_harmony"] = df["num_distinct_chords"] > 0


# ---------------------------------------------------------------------
# 2. Functional harmony normalization
# ---------------------------------------------------------------------
# Coarse-level functional categories:
#   T  -> Tonic
#   S  -> Subdominant
#   D  -> Dominant
#   Other -> None (functionally undefined)

FUNCTION_COARSE_MAP = {
    "T": "T",
    "S": "S",
    "D": "D",
    "Other": "None"
}

df["function_coarse"] = (
    df["function"]
    .map(FUNCTION_COARSE_MAP)
    .fillna("None")
)

# Fine-grained function (placeholder for later refinement)
df["function_fine"] = df["function_coarse"]


# ---------------------------------------------------------------------
# 3. Chord-type representation cleanup
# ---------------------------------------------------------------------
# Normalize chord quality labels without inference.
# Augmented / diminished inference will occur in Stage C.2.

CHORD_TYPE_MAP = {
    "maj": "major",
    "min": "minor",
    "triad": "unknown",
    "other": "unknown"
}

df["most_common_chord_type"] = (
    df["most_common_chord_type"]
    .map(CHORD_TYPE_MAP)
)


# ---------------------------------------------------------------------
# 4. Optional sanity checks (comment out if running in batch)
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("\n=== Sanity Checks ===\n")

    print("Explicit harmony presence:")
    print(df["has_explicit_harmony"].value_counts(), "\n")

    print("Coarse harmonic function distribution:")
    print(df["function_coarse"].value_counts(), "\n")

    print("Chord-type distribution (including NaNs):")
    print(df["most_common_chord_type"].value_counts(dropna=False), "\n")


# ---------------------------------------------------------------------
# 5. Save normalized dataset
# ---------------------------------------------------------------------

df.to_csv(OUT_CSV, index=False)

print(f"\n✔ Harmonic-normalized dataset saved to:\n{OUT_CSV}")
