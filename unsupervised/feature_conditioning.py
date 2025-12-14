import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

IN_PATH = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data"
    r"\measure_features_rhythmic_normalized.csv"
)

OUT_PATH = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data"
    r"\measure_features_conditioned.csv"
)

# ------------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------------

df = pd.read_csv(IN_PATH)
print("Loaded dataset shape:", df.shape)

# ------------------------------------------------------------------
# 1. Melodic feature conditioning
# ------------------------------------------------------------------
# These variables are only meaningful when melodic motion exists

melodic_motion_features = [
    "melodic_range",
    "mean_interval",
    "large_jump_pct",
]

df.loc[~df["has_melodic_motion"], melodic_motion_features] = 0

# ------------------------------------------------------------------
# 2. Duration feature conditioning
# ------------------------------------------------------------------
# Durations are only meaningful if melodic activity exists

duration_features = [
    "avg_duration",
    "most_common_duration",
]

df.loc[~df["has_melodic_activity"], duration_features] = 0

# ------------------------------------------------------------------
# 3. Harmonic numeric conditioning
# ------------------------------------------------------------------
# Harmonic numeric features are undefined without explicit harmony

harmonic_numeric_features = [
    "degree_relative_to_key",
    "num_distinct_chords",
]

df.loc[~df["has_explicit_harmony"], harmonic_numeric_features] = 0

# ------------------------------------------------------------------
# 4. Harmonic categorical conditioning
# ------------------------------------------------------------------
# Explicitly encode absence of harmony

harmonic_categorical_features = [
    "most_common_chord_root",
    "most_common_chord_type",
    "function_coarse",
]

for col in harmonic_categorical_features:
    df[col] = df[col].fillna("NO_HARMONY")

# ------------------------------------------------------------------
# 5. Harmonic fine function (kept but flagged for exclusion later)
# ------------------------------------------------------------------
# This column is intentionally preserved for interpretability
# but should not be used for clustering

df["function_fine"] = df["function_fine"].fillna("NO_HARMONY")

# ------------------------------------------------------------------
# 6. Rhythmic entropy numerical stability
# ------------------------------------------------------------------
# Clip floating-point noise (e.g. -0.000000)

df["rhythmic_entropy"] = df["rhythmic_entropy"].clip(lower=0)

# ------------------------------------------------------------------
# 7. Sanity checks
# ------------------------------------------------------------------

print("\nSanity check — remaining missing values:")
print(df.isna().sum().sort_values(ascending=False).head(10))

print("\nMelodic motion conditioning check:")
print(df.loc[~df["has_melodic_motion"], melodic_motion_features].describe())

print("\nExplicit harmony conditioning check:")
print(
    df.loc[~df["has_explicit_harmony"], harmonic_numeric_features]
    .describe()
)


# ------------------------------------------------------------------
# 8. Fix remaining NaNs in degree_relative_to_key
# ------------------------------------------------------------------

df["degree_relative_to_key"] = df["degree_relative_to_key"].fillna(-1)

# Verify
print("Remaining NaNs:", df.isna().sum().sum())

# ------------------------------------------------------------------
# Save conditioned dataset
# ------------------------------------------------------------------

df.to_csv(OUT_PATH, index=False)
print("\nConditioned dataset saved to:")
print(OUT_PATH)
