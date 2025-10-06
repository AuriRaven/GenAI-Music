import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

def train_random_forest(df: pd.DataFrame, target_col: str, test_size: float = 0.2, random_state: int = 42):
    """
    Train a Random Forest classifier on a dataset and evaluate its performance.
    Automatically encodes categorical/string features using one-hot encoding.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing features and target.
    target_col : str
        Name of the target variable column.
    test_size : float, optional
        Fraction of data used for validation (default is 0.2).
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    model : RandomForestClassifier
        Trained Random Forest model.
    metrics : dict
        Dictionary with accuracy, precision, recall, F1-score, and classification report.
    """

    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Detect categorical/string columns and one-hot encode
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        X = pd.get_dummies(X, columns=categorical_cols)

    # Ensure all remaining features are numeric
    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns
    X = X[numeric_cols]

    # Train/validation split (stratified)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Initialize Random Forest
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=random_state,
        n_jobs=-1
    )

    # Train the model
    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)

    # Metrics
    metrics = {
        "train_accuracy": accuracy_score(y_train, y_pred_train),
        "val_accuracy": accuracy_score(y_val, y_pred_val),
        "train_precision": precision_score(y_train, y_pred_train, average="weighted", zero_division=0),
        "val_precision": precision_score(y_val, y_pred_val, average="weighted", zero_division=0),
        "train_recall": recall_score(y_train, y_pred_train, average="weighted", zero_division=0),
        "val_recall": recall_score(y_val, y_pred_val, average="weighted", zero_division=0),
        "train_f1": f1_score(y_train, y_pred_train, average="weighted", zero_division=0),
        "val_f1": f1_score(y_val, y_pred_val, average="weighted", zero_division=0),
        "classification_report": classification_report(y_val, y_pred_val, zero_division=0)
    }

    return model, metrics
