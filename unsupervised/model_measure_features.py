import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
IN_PATH = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data"
    r"\measure_features_conditioned.csv"
)

OUT_PATH = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\modeled_data"
    r"\modeled_measure_features.csv"
)

PCA_OUT_PATH = Path(
    r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\modeled_data"
    r"\pca_measure_features.csv"
)

# ------------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------------
df = pd.read_csv(IN_PATH)
print("Loaded dataset shape:", df.shape)

# ------------------------------------------------------------------
# 1. Select numeric features
# ------------------------------------------------------------------
numeric_features = [
    'melodic_range','mean_interval','large_jump_pct','avg_duration',
    'note_density','rhythmic_entropy','degree_relative_to_key','num_distinct_chords',
] + [f'pc_{i}' for i in range(12)]

X = df[numeric_features]

# ------------------------------------------------------------------
# 2. Check for outliers and choose scaler
# ------------------------------------------------------------------
z_scores = np.abs((X - X.mean()) / X.std())
outlier_mask = (z_scores > 3).any(axis=1)
outlier_fraction = outlier_mask.mean()
print(f"Outlier fraction: {outlier_fraction:.2%}")

if outlier_fraction > 0.05:
    print("Using RobustScaler due to >5% outliers")
    scaler = RobustScaler()
else:
    print("Using StandardScaler")
    scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

# ------------------------------------------------------------------
# 3. PCA
# ------------------------------------------------------------------
pca = PCA(n_components=0.9, random_state=42)
X_pca = pca.fit_transform(X_scaled)
print(f"PCA reduced from {X_scaled.shape[1]} to {X_pca.shape[1]} components")

# Save PCA dataframe for visualization
pca_df = pd.DataFrame(X_pca, columns=[f"PCA_{i+1}" for i in range(X_pca.shape[1])])
pca_df['cluster'] = None  # will add clusters after clustering
pca_df.to_csv(PCA_OUT_PATH, index=False)
print(f"PCA dataframe saved to: {PCA_OUT_PATH}")

# ------------------------------------------------------------------
# 4. KMeans clustering
# ------------------------------------------------------------------
k_opt = 4  # adjust if needed
kmeans = KMeans(n_clusters=k_opt, random_state=42)
clusters = kmeans.fit_predict(X_pca)
df['cluster'] = clusters
pca_df['cluster'] = clusters  # add clusters to PCA df

print("Clustering complete. Cluster counts:")
print(df['cluster'].value_counts())

# Save updated PCA dataframe with cluster labels
pca_df.to_csv(PCA_OUT_PATH, index=False)

# ------------------------------------------------------------------
# 5. Save modeled dataset
# ------------------------------------------------------------------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nModeled dataset saved to: {OUT_PATH}")
