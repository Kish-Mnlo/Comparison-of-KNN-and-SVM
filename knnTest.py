import pandas as pd
import yfinance as yf
from sklearn.model_selection import (
    train_test_split,
    TimeSeriesSplit, 
    GridSearchCV
    )
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)
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

# =====================================================
# Target Variable
# 1 = Price goes up tomorrow
# 0 = Price goes down or stays the same
# =====================================================
future_return = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

df["Target"] = (future_return > 0.002).astype(int)

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

# =====================================================
# Train-Test Split (Time Series)
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)

# =====================================================
# Pipeline
# =====================================================

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
        "knn",
        KNeighborsClassifier(
            metric="euclidean",
            weights="distance"
        )
    )
])

# =====================================================
# Hyperparameter tuning grid
# =====================================================

param_grid = {
    # Allows bypassing of feature selection completely ("all")
    "feature_selection__k": [5, 7, 9, "all"],
    "knn__n_neighbors": list(range(3, 32, 2)),
}

tscv = TimeSeriesSplit(n_splits=5)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=tscv,
    scoring="balanced_accuracy"
)

# =====================================================
# Find the Best k
# =====================================================
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

# =====================================================
# Predictions
# =====================================================
y_pred = best_model.predict(X_test)
y_prob = best_model.predict_proba(X_test)[:, 1]

# =====================================================
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

# =====================================================
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

# Daily market returns
df["Market_Return"] = df["Close"].pct_change()

# Test period
test_df = df.loc[y_test.index].copy()

# Predictions
test_df["Prediction"] = y_pred

# Trading position (next-day execution)
test_df["Position"] = test_df["Prediction"].shift(1)

# Strategy returns
test_df["Strategy_Return"] = (
    test_df["Position"] *
    test_df["Market_Return"]
)

test_df = test_df.dropna()

import numpy as np

risk_free_rate = 0.07511      # 7.511% annual
daily_rf = risk_free_rate / 252

excess_returns = test_df["Strategy_Return"] - daily_rf

sharpe_ratio = excess_returns / excess_returns.std()

sharpe_ratio = sharpe_ratio.mean()

annualized_sharpe = sharpe_ratio * np.sqrt(252)

print(f"Daily Risk-Free Rate: {daily_rf:.8f}")
print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
print(f"Annualized Sharpe Ratio: {annualized_sharpe:.4f}")

joblib.dump(best_model, "knn.pkl")