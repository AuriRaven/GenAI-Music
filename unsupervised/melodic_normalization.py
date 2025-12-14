"""
Stage C.3 – Melodic Variable Normalization

This script stabilizes melodic-related variables in a
measure-level dataset derived from Bach solo string music.

Philosophy:
- Zeros are often musically meaningful (not missing)
- Do NOT impute durations or intervals
- Explicitly encode melodic activity
- Allow later conditioning in clustering and PCA

No rows are dropped.
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
    / "measure_features_harmonic_normalized.csv"
)

OUT_CSV = (
    BASE_PATH
    / "unsupervised"
    / "curated_data"
    / "measure_features_melodic_normalized.csv"
)


# ---------------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------------

df = pd.read_csv(IN_CSV)


# ---------------------------------------------------------------------
# 1. Melodic activity indicators
# ---------------------------------------------------------------------
# These explicitly separate:
# - rests / sustained carry-over
# - single-note measures
# - true melodic motion

df["has_melodic_activity"] = df["num_notes_melody"] > 0
df["has_melodic_motion"] = df["num_notes_melody"] > 1


# ---------------------------------------------------------------------
# 2. Melodic variables (kept as-is, but now interpretable)
# ---------------------------------------------------------------------
# melodic_range == 0:
#   → single-note or sustained-note measures
#
# mean_interval == 0:
#   → no intervallic motion
#
# large_jump_pct == 0:
#   → no large leaps occurred (informative!)
#
# avg_duration / most_common_duration == 0:
#   → no newly-onset melodic durations in this measure
#
# No transformation is applied here.
# Conditioning will happen in modeling stages.


# ---------------------------------------------------------------------
# 3. Optional sanity checks
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("\n=== Sanity Checks ===\n")

    print("Melodic activity:")
    print(df["has_melodic_activity"].value_counts(), "\n")

    print("Melodic motion:")
    print(df["has_melodic_motion"].value_counts(), "\n")

    print("Measures with melodic_range = 0 and motion:")
    print(
        df.loc[
            (df["melodic_range"] == 0) &
            (df["has_melodic_motion"]),
            "melodic_range"
        ].count(),
        "\n"
    )


# ---------------------------------------------------------------------
# 4. Save normalized dataset
# ---------------------------------------------------------------------

df.to_csv(OUT_CSV, index=False)

print(f"\n✔ Melodic-normalized dataset saved to:\n{OUT_CSV}")
