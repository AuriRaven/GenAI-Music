"""
Stage B – Identifier & Metadata Normalization

This script performs metadata cleaning on the raw measure-level dataset
produced by extract_features.py.

Scope:
- Operates ONLY on identifier / metadata columns
- Does NOT modify musical features
- Uses `file` as the authoritative metadata source
- Ensures canonical, reproducible identifiers for analysis
"""

from pathlib import Path
import pandas as pd
import re

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
RAW_CSV = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\raw_data\measure_features_raw.csv"
)
OUT_CSV = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data\measure_features_identifiers.csv"
)
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def extract_bwv_from_file(path: str) -> str | None:
    """
    Extract canonical BWV identifier from a full file path.

    Example:
        '.../Suite No. 1 in G major BWV1007/1 Allemande.xml' → 'BWV1007'
    """
    if pd.isna(path):
        return None

    match = re.search(r"BWV\s*(\d+)", str(path), re.IGNORECASE)
    if match:
        return f"BWV{match.group(1)}"

    return None


def extract_movement_from_file(path: str) -> str | None:
    """
    Extract and normalize movement name from a full file path.

    Cleaning steps:
    - Take filename only
    - Remove extensions (.xml, .mid, .mxl)
    - Remove 'Accomp'
    - Remove leading digits and punctuation
    - Normalize capitalization

    Example:
        '.../1 Allemande Accomp.xml' → 'Allemande'
    """
    if pd.isna(path):
        return None

    filename = Path(str(path)).name

    # Remove extension
    s = re.sub(r"\.(mid|xml|mxl)$", "", filename, flags=re.IGNORECASE)

    # Remove accompaniment markers
    s = re.sub(r"\bAccomp\b", "", s, flags=re.IGNORECASE)

    # Remove leading numbers / punctuation
    s = re.sub(r"^[\d\s\-\._]+", "", s)

    # Normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s.title() if s else None


# ---------------------------------------------------------------------
# Main procedure
# ---------------------------------------------------------------------

def main():
    print("📥 Loading raw dataset...")
    df = pd.read_csv(RAW_CSV)

    if "file" not in df.columns:
        raise ValueError("Expected column 'file' not found.")

    # -----------------------------
    # 1. Extract BWV and movement from `file`
    # -----------------------------
    print("🔍 Extracting BWV and movement from file paths...")
    df["bwv"] = df["file"].apply(extract_bwv_from_file)
    df["movement"] = df["file"].apply(extract_movement_from_file)

    # -----------------------------
    # 2. Sanity checks
    # -----------------------------
    missing_bwv = df["bwv"].isna().sum()
    missing_mov = df["movement"].isna().sum()

    print(f"BWV missing: {missing_bwv}")
    print(f"Movement missing: {missing_mov}")

    if missing_bwv > 0:
        print("⚠️ Example rows with missing BWV:")
        print(df.loc[df["bwv"].isna(), "file"].head())

    # -----------------------------
    # 3. Drop obsolete identifier columns
    # -----------------------------
    drop_cols = [c for c in ["suite", "file"] if c in df.columns]
    df.drop(columns=drop_cols, inplace=True)

    # -----------------------------
    # 4. Reorder columns: identifiers first
    # -----------------------------
    identifier_cols = ["bwv", "movement", "measure_index"]

    remaining_cols = [c for c in df.columns if c not in identifier_cols]

    df = df[identifier_cols + remaining_cols]

    # -----------------------------
    # Save curated dataset
    # -----------------------------
    print("💾 Saving cleaned identifier dataset...")
    df.to_csv(OUT_CSV, index=False)

    print("✅ Identifier cleaning complete.")
    print(f"   Output written to: {OUT_CSV}")


if __name__ == "__main__":
    main()
