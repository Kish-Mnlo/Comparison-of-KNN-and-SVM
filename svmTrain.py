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

#build featurews

df = features3.build_features(df)

# Target Variable
# 1 = Price goes up tomorrow
# 0 = Price goes down or stays the same
#-----------------------------------------
future_return = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

# Predict target direction (0.2% change threshold)
df["Target"] = (future_return > 0.002).astype(int)

# Drop any remaining NaN targets (usually just the last row)
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

#train test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    shuffle=False
)

#PIPELINE
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

#tuning
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


# Train Model
# ======================================
print("Starting grid search hyperparameter tuning...")
grid.fit(X_train, y_train)

best_model = grid.best_estimator_

print("\nBest Parameters Found:")
print("----------------")
print(grid.best_params_)

joblib.dump(best_model, "svm.pkl")