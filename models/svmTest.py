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
SVMmodel = joblib.load("svm.pkl")


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

# Train-Test Split (Time Series)
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
selector = SVMmodel.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# Predictions
y_pred = SVMmodel.predict(X_test)
y_prob = SVMmodel.predict_proba(X_test)[:, 1]

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
    display_labels=["-1", "1"]
).plot(
    cmap="Blues",
    colorbar=False
)

plt.title("SVM Confusion Matrix")
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
