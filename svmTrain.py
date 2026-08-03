import numpy as np
import pandas as pd
import yfinance as yf
import sklearn

from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    TimeSeriesSplit
)
# Changed import from MinMaxScaler to StandardScaler
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
    confusion_matrix
)

import joblib

import features3

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

# ======================================
# Build Features
# ======================================

df = features3.build_features(df)

# ======================================
# Target Variable
# 1 = Price increases tomorrow beyond target
# 0 = Price stays flat or decreases tomorrow
# ======================================
future_return = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

# Predict target direction (0.2% change threshold)
df["Target"] = (future_return > 0.002).astype(int)

# Drop any remaining NaN targets (usually just the last row)
df = df.dropna()

# ======================================
# Feature Matrix
# ======================================
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

# ======================================
# Chronological Train/Test Split
# ======================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    shuffle=False
)

# ======================================
# Pipeline Setup
# ======================================
pipeline = Pipeline([
    (
        "scaler",
        # Replaced MinMaxScaler() with StandardScaler()
        StandardScaler()
    ),
    (
        "feature_selection",
        SelectKBest(score_func=mutual_info_classif)
    ),
    (
        "svm",
        SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=42
        )
    )
])

# ======================================
# Hyperparameter Tuning Grid
# ======================================
param_grid = {
    # Allows bypassing of feature selection completely ("all")
    "feature_selection__k": [5, "all"],
    #initial: 
    # "svm__C": [0.1, 1, 5, 10, 50],
    # "svm__gamma": ["scale", 0.1, 0.01, 0.001]
    "svm__C": [0.01,0.1,1,10,50,100,500],
    "svm__gamma": ["scale", 1, 0.5, 0.1, 0.05, 0.01, 0.005, 0.001]
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

# ======================================
# Train Model
# ======================================
print("Starting grid search hyperparameter tuning...")
grid.fit(X_train, y_train)

best_model = grid.best_estimator_

print("\nBest Parameters Found:")
print("----------------")
print(grid.best_params_)

# ======================================
# Selected Features
# ======================================
selector = best_model.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# ======================================
# Predictions & Probability
# ======================================
y_pred = best_model.predict(X_test)
y_prob = best_model.predict_proba(X_test)[:, 1]

# ======================================
# Evaluation Metrics
# ======================================
print("\nFinal SVM Results")
print("-----------------")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_test, y_pred):.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# ======================================
# Prediction Table Outputs
# ======================================
results = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred,
    "Probability": np.round(y_prob * 100, 2)
}, index=y_test.index)

print("\nLast 20 Predictions:")
print(results.tail(20))

# ======================================
# Current/Latest Trading Prediction
# ======================================
latest = X.tail(1)
prediction = best_model.predict(latest)[0]
probability = best_model.predict_proba(latest)[0][1]

print("\nLatest Trading Day Forecast")
print("---------------------------")
print("Date       :", latest.index[0].date())
print("Prediction :", "UP" if prediction == 1 else "DOWN")
print(f"Confidence : {probability * 100:.2f}%")

joblib.dump(best_model, "svm.pkl")