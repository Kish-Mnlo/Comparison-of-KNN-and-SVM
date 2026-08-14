from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from sklearn.model_selection import train_test_split
import pandas as pd
import yfinance as yf
import numpy as np
import joblib
from features3 import build_features

# Load trained model
SVMmodel = joblib.load("svm.pkl")

#download psei
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


#build features
df = build_features(df)

# Target Variable
# 1 = Price goes up tomorrow
# 0 = Price goes down or stays the same
#-----------------------------------------
df["Future_Returns"] = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

df["Target"] = (df["Future_Returns"] > 0.002).astype(int)
df["Daily_Returns"] = df["Close"].pct_change()

df = df.dropna()

#feature matrix
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

#train and test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)

#selected features
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
# =====================================================
print("\nFinal Model Results")
print("-------------------")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_test, y_pred):.4f}\n")

print("Confusion Matrix")
print(confusion_matrix(y_test, y_pred))
print()

print("Classification Report")
print(classification_report(y_test, y_pred))


# Prediction Results
# =====================================================
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


# Information Ratio
# =====================================================

test_returns = df.loc[X_test.index, "Future_Returns"]

results = pd.DataFrame({
    "Future_Return": test_returns,
    "Prediction": y_pred
}, index=X_test.index)

results["Signal"] = np.where(results["Prediction"] == 1, 1, -1)

# Strategy return
results["Strategy_Return"] = (
    results["Signal"] * results["Future_Return"]
)

# Buy-and-hold benchmark
results["Benchmark_Return"] = results["Future_Return"]

# Cumulative returns
results["Cumulative_Strategy_Return"] = (
    1 + results["Strategy_Return"]
).cumprod()

results["Cumulative_Benchmark_Return"] = (
    1 + results["Benchmark_Return"]
).cumprod()

# Information Ratio
excess_returns = (
    results["Strategy_Return"]
    - results["Benchmark_Return"]
)

tracking_error = excess_returns.std()

if tracking_error != 0:
    information_ratio = excess_returns.mean() / tracking_error
    information_ratio = information_ratio * np.sqrt(252)
else:
    information_ratio = np.nan

print(f"\nInformation Ratio: {information_ratio:.4f}")

print("Strategy cumulative return:",
      (1 + results["Strategy_Return"]).prod() - 1)

print("Benchmark cumulative return:",
      (1 + results["Benchmark_Return"]).prod() - 1)

print("Mean strategy return:",
      results["Strategy_Return"].mean())

print("Mean benchmark return:",
      results["Benchmark_Return"].mean())

print("Tracking error:",
      excess_returns.std())