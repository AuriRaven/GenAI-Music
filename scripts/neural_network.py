import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input

def prepare_features(df: pd.DataFrame, target_col: str, prev_chords: bool = False):
    """
    Prepares features and target for MLP training.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    target_col : str
        Column name of the target (chord_name).
    prev_chords : bool
        Whether to include previous chord numeric features.

    Returns
    -------
    X : np.ndarray
        Features matrix (float32, numeric).
    y : np.ndarray
        One-hot encoded target matrix.
    encoder : OneHotEncoder
        Fitted encoder for the target.
    """
    df_copy = df.copy()

    # Optionally create previous chord features
    if prev_chords:
        numeric_cols = ['root', 'bass'] + [f'pc_{i}' for i in range(12)]
        for col in numeric_cols:
            df_copy[f'prev_{col}'] = df_copy[col].shift(1).fillna(0)

    # Separate features and target
    X = df_copy.drop(columns=[target_col])
    y = df_copy[target_col]

    # One-hot encode categorical features
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        X = pd.get_dummies(X, columns=categorical_cols)

    # Standardize numeric features
    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        scaler = StandardScaler()
        X[numeric_cols] = scaler.fit_transform(X[numeric_cols])

    # Ensure numeric and no NaNs
    X = X.fillna(0).astype(np.float32)

    # Encode target
    encoder = OneHotEncoder(sparse_output=False)
    y_encoded = encoder.fit_transform(y.values.reshape(-1,1))

    return X.values, y_encoded, encoder


def build_mlp(input_dim: int, output_dim: int, hidden_layers=[128, 64, 32], dropout_rate=0.2):
    """
    Builds a feedforward neural network (MLP) for chord prediction.

    Parameters
    ----------
    input_dim : int
        Number of input features.
    output_dim : int
        Number of output classes (chords).
    hidden_layers : list of int
        Number of neurons in each hidden layer.
    dropout_rate : float
        Dropout rate for regularization.

    Returns
    -------
    model : keras.Sequential
        Compiled MLP model.
    """
    model = Sequential()
    model.add(Input(shape=(input_dim,)))  # Use Input layer instead of input_dim
    model.add(Dense(hidden_layers[0], activation='relu'))
    model.add(Dropout(dropout_rate))

    for neurons in hidden_layers[1:]:
        model.add(Dense(neurons, activation='relu'))
        model.add(Dropout(dropout_rate))

    model.add(Dense(output_dim, activation='softmax'))

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def train_nn(df: pd.DataFrame, target_col: str, prev_chords: bool = False, test_size=0.2, epochs=50, batch_size=32):
    """
    Trains the MLP on the dataset and evaluates it.

    Returns
    -------
    model : keras.Sequential
        Trained model.
    metrics : dict
        Training and validation accuracy.
    """
    # Prepare features
    X, y, encoder = prepare_features(df, target_col, prev_chords)
    
    # Train/validation split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # Build model
    model = build_mlp(input_dim=X.shape[1], output_dim=y.shape[1])

    # Train
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=2
    )

    # Metrics
    metrics = {
        "train_accuracy": history.history['accuracy'][-1],
        "val_accuracy": history.history['val_accuracy'][-1]
    }

    return model, metrics, encoder
