import pandas as pd
import yfinance as yf
from sklearn.model_selection import (
    train_test_split,
    TimeSeriesSplit, 
    GridSearchCV
    )
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from features3 import build_features
import joblib

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

print("Training:")
print(X_train.index.min(), "→", X_train.index.max())

print("\nValidation:")
print(X_val.index.min(), "→", X_val.index.max())

print("\nTest:")
print(X_test.index.min(), "→", X_test.index.max())


# Pipeline
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
        "knn",
        KNeighborsClassifier(
            metric="euclidean",
            weights="distance"
        )
    )
])

# Hyperparameter tuning grid
param_grid = {
    "feature_selection__k": [1, 2, 3, 4, 5, 6, 7, 8, 9, "all"],
    "knn__n_neighbors": list(range(3, 32, 2)),
}

tscv = TimeSeriesSplit(n_splits=5)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=tscv,
    scoring="balanced_accuracy"
)

# Best k
print("Starting grid search hyperparameter tuning...")
grid.fit(X_train, y_train)

best_model = grid.best_estimator_

selector = best_model.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

print("\nBest Parameters Found:")
print("----------------")
print(grid.best_params_)

y_val_pred = best_model.predict(X_val)

print("\nValidation Model Results")
print("-------------------")
print(f"Accuracy : {accuracy_score(y_val, y_val_pred):.4f}")
print(f"Precision: {precision_score(y_val, y_val_pred):.4f}")
print(f"Recall   : {recall_score(y_val, y_val_pred):.4f}")
print(f"F1 Score : {f1_score(y_val, y_val_pred):.4f}\n")

# Training balanced accuracy
train_balanced_accuracy = balanced_accuracy_score(y_val, y_val_pred)
print(f"Validation Balanced Accuracy: {train_balanced_accuracy:.4f}")

print("\nValidation Classification Report:")
print(classification_report(y_val, y_val_pred))

joblib.dump(best_model, "knn.pkl")
