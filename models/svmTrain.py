import os
import numpy as np
import pandas as pd
import yfinance as yf
import sklearn

from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    TimeSeriesSplit
)

from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    balanced_accuracy_score
)

import joblib

from features3 import build_features

df = pd.read_csv("psei_real_sorted.csv")
print(df.columns.tolist())
print(df.head())


# Build Features
df = build_features(df)


# Target Variable
# Calculate next-day return
df["Future_Return"] = (
    df["Close"].shift(-1) - df["Close"]
) / df["Close"]


# Classification Target
df["Target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, -1)

# Daily return
df["Daily_Return"] = df["Close"].pct_change()

# Remove missing values
df = df.dropna()

# Feature Matrix
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

# Chronological Train/Test Split
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y,
    test_size=0.20,
    shuffle=False
)

X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val,
    test_size=0.25,
    shuffle=False
)

# Pipeline Setup
pipeline = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),
    (
        "feature_selection",
        SelectKBest(score_func=mutual_info_classif)
    ),
    (
        "svm",
        SVC(
            kernel="linear",
            probability=True,
            class_weight="balanced",
            random_state=42,
        )
    )
])

# Hyperparameter Tuning Grid
param_grid = {
    "feature_selection__k": [1, 2, 3, 4, 5, 6, 7, 8, 9, "all"],
    "svm__C":  [0.01, 0.1, 1, 10, 50, 100, 500]
}

# Time-series split logic for cross-validation
tscv = TimeSeriesSplit(n_splits=5)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=tscv,
    scoring="f1",
    n_jobs=-1,
    verbose=1
)

# Train Model
print("Starting grid search hyperparameter tuning...")
grid.fit(X_train, y_train)

best_model = grid.best_estimator_

print("\nBest Parameters Found:")
print("----------------")
print(grid.best_params_)

# Selected Features
selector = best_model.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# Predictions & Probability
y_pred = best_model.predict(X_val)
y_prob = best_model.predict_proba(X_val)[:, 1]

# Evaluation Metrics
print("\nValidation SVM Results")
print("-----------------")
print(f"Accuracy : {accuracy_score(y_val, y_pred):.4f}")
print(f"Precision: {precision_score(y_val, y_pred):.4f}")
print(f"Recall   : {recall_score(y_val, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_val, y_pred):.4f}")


print("\nValidation Classification Report:")
print(classification_report(y_val, y_pred))

joblib.dump(best_model, "svm.pkl")
