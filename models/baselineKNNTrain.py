import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.model_selection import (
    train_test_split,
    TimeSeriesSplit
    )
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from features3 import build_features
import joblib


# ======================================
# Download PSEI Data
# ======================================

ticker = "PSEI.PS"

df = yf.download(
    ticker,
    start="2016-01-01",
    end="2025-12-31",
    auto_adjust=True,
    progress=False
)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)


# =====================================================
# Build Features
# =====================================================

df = build_features(df)

# ======================================
# Classification Target
# ======================================

df["Target"] = np.where(
    df["Close"].shift(-1) > df["Close"], 1, -1
)

# Remove NaN values
df = df.dropna()

# =====================================================
# Feature Matrix
# =====================================================

feature_columns = [
    "SMA",
    "WMA",
    "StochD",
    "AD",
    "PctDiffLow",
    "FFT_Min",
    "FFT_Max",
    "Skewness",
    "Kurtosis",
    "SD"
]

X = df[feature_columns]
y = df["Target"]


X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y,
    test_size=0.20,
    shuffle=False
)


# =====================================================
# Basic Train
# =====================================================

tscv = TimeSeriesSplit(n_splits=5)

scores = []

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train_val), start = 1):

    X_train = X_train_val.iloc[train_idx]
    X_val = X_train_val.iloc[val_idx]

    y_train = y_train_val.iloc[train_idx]
    y_val = y_train_val.iloc[val_idx]

    train_start = X_train.index.min()
    train_end = X_train.index.max()

    val_start = X_val.index.min()
    val_end = X_val.index.max()

    # Pipeline
    model = Pipeline([
        (
            "scaler",
            # Replaced MinMaxScaler() with StandardScaler()
            StandardScaler()
        ),
        (
            "knn",
            KNeighborsClassifier(
                metric="minkowski",
                weights="distance",
                n_neighbors = 5,
                p = 2
            )
        )
    ])

    model.fit(X_train, y_train)
    

    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    scores.append(accuracy)

    # Evaluation Metrics
    print(f"Fold {fold}:")
    print(f"Training   : {train_start.date()} → {train_end.date()}")
    print(f"Validation : {val_start.date()} → {val_end.date()}")
    print(f"Train size : {len(X_train)}")
    print(f"Val size   : {len(X_val)}")

    print("\nValidation Model Results")
    print("-------------------")
    print(f"Accuracy : {accuracy_score(y_val, y_pred):.4f}")
    print(f"Precision: {precision_score(y_val, y_pred):.4f}")
    print(f"Recall   : {recall_score(y_val, y_pred):.4f}")
    print(f"F1 Score : {f1_score(y_val, y_pred):.4f}\n")

    # Training balanced accuracy
    train_balanced_accuracy = balanced_accuracy_score(y_val, y_pred)
    print(f"Validation Balanced Accuracy: {train_balanced_accuracy:.4f}")

    print("\nValidation Classification Report:")
    print(classification_report(y_val, y_pred))

print(f"Mean Accuracy: {np.mean(scores):.4f}")

# =====================================================
# Final Model
# =====================================================

final_model = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),
    (
        "knn",
        KNeighborsClassifier(
            metric="minkowski",
            weights="distance",
            n_neighbors=5,
            p=2
        )
    )
])

final_model.fit(X_train_val, y_train_val)

joblib.dump(final_model, "knn.pkl")
print("KNN model successfully exported!")