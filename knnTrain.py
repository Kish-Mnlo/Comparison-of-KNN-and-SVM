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
# Target Variable and Daily Returns
# 1 = Price goes up tomorrow
# 0 = Price goes down or stays the same
# =====================================================
df["Future_Returns"] = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

df["Target"] = (df["Future_Returns"] > 0.002).astype(int)
df["Daily_Returns"] = df["Close"].pct_change()

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
    "feature_selection__k": [5, "all"],
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



joblib.dump(best_model, "knn.pkl")