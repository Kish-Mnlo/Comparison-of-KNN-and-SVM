from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

from sklearn.model_selection import train_test_split
import pandas as pd
import yfinance as yf
import numpy as np
import joblib
import matplotlib.pyplot as plt
from features3 import build_features

# Load trained model
KNNmodel = joblib.load("knn.pkl")

# Download PSEI Data
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

# Build Features
df = build_features(df)

# Target Variable
# Calculate next-day return
df["Future_Return"] = (
    df["Close"].shift(-1) - df["Close"]
) / df["Close"]


# Classification Target
# 1 = Next-day return > 0.2%
# 0 = Next-day return <= 0.2%
df["Target"] = (
    df["Future_Return"] > 0.002
).astype(int)

# Daily return
df["Daily_Return"] = df["Close"].pct_change()

# Remove NaN values
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

# Train-Test Split
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

# Selected Features
selector = KNNmodel.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# Predictions
y_pred = KNNmodel.predict(X_test)
y_prob = KNNmodel.predict_proba(X_test)[:, 1]

# Evaluation
print("\nFinal Model Results")
print("-------------------")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_test, y_pred):.4f}\n")

print("Confusion Matrix")
confumatrix = confusion_matrix(y_test, y_pred)
print(confumatrix)

# SVM
ConfusionMatrixDisplay(
    confusion_matrix=confumatrix,
    display_labels=["≤ 0.2%", "> 0.2%"]
).plot(
    cmap="Blues",
    colorbar=False
)

plt.title("KNN Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.show()  

print("Classification Report")
print(classification_report(y_test, y_pred))

# Prediction Results
results = pd.DataFrame(
    {
        "Actual": y_test.values,
        "Predicted": y_pred,
        "Probability_Up": y_prob,
    },
    index=y_test.index,
)

print("\nLast 20 Predictions")
print(results.tail(20))
