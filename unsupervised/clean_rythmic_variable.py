"""
Stage C.4 – Rhythmic Variable Normalization

This script corrects numerical artifacts in rhythmic descriptors
without altering musically meaningful information.

Scope:
- Operates ONLY on rhythmic variables
- Applies deterministic, theory-consistent corrections
- Does NOT perform imputation or scaling

Input:
    data/curated/measure_features_melodic_normalized.csv

Output:
    data/curated/measure_features_rhythmic_normalized.csv
"""

from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

INPUT_CSV = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data"
    r"\measure_features_melodic_normalized.csv"
)

OUTPUT_CSV = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data"
    r"\measure_features_rhythmic_normalized.csv"
)

OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Main procedure
# ---------------------------------------------------------------------

def main():
    print("📥 Loading melodic-normalized dataset...")
    df = pd.read_csv(INPUT_CSV)

    if "rhythmic_entropy" not in df.columns:
        raise ValueError("Expected column 'rhythmic_entropy' not found.")

    # --------------------------------------------------------------
    # Rhythmic entropy correction
    # --------------------------------------------------------------
    # Numerical precision may produce small negative values (-ε)
    # Entropy is theoretically bounded below by 0
    # We enforce this bound deterministically
    # --------------------------------------------------------------

    df["rhythmic_entropy"] = df["rhythmic_entropy"].clip(lower=0.0)

    # --------------------------------------------------------------
    # Save corrected dataset
    # --------------------------------------------------------------
    print("💾 Saving rhythmic-normalized dataset...")
    df.to_csv(OUTPUT_CSV, index=False)

    print("✅ Rhythmic normalization complete.")
    print(f"   Output written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
