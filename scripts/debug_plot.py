import pandas as pd
import plotly.express as px

DATA_PATH = r"C:\Users\Aura De La Garza G\Projects\GenAI-Music\unsupervised\curated_data\measure_features_conditioned.csv"

if __name__ == '__main__':
    df = pd.read_csv(DATA_PATH)
    counts = df["function_coarse"].value_counts().rename_axis("function_coarse").reset_index(name="count")
    print("Counts head:\n", counts.head())

    fig = px.bar(
        counts,
        x="function_coarse",
        y="count",
        labels={"function_coarse": "Harmonic Function", "count": "Count"},
        title="Distribution of Coarse Harmonic Functions",
    )

    out = "tmp_plot.html"
    fig.write_html(out)
    print(f"Saved plot to: {out}")