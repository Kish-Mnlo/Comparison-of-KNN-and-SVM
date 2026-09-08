import numpy as np
import pandas as pd
import yfinance as yf
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
)
import joblib
from features3 import build_features

# Read Dataset CSV file
df = pd.read_csv("psei_real_sorted.csv")
print(df.columns.tolist())
print(df.head())

# Build Features (Predictor Values)
df = build_features(df)

# Target Variable
# Classification Target
df["Target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, -1)

# Remove missing (Null) values
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

# Make X the input variables to be used for prediction and Y for the output (What the model is trying to predict)
X = df[feature_columns]
y = df["Target"]

# Chronological Train/Test Split
# Split 80% for Train and Validation and 20% For Test
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y,
    test_size=0.20,
    shuffle=False
)

# Split 75% for Training and 25% For Validation
X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val,
    test_size=0.25,
    shuffle=False
)

# Print the dates to make sure of chronological order
print("Training:")
print(X_train.index.min(), "→", X_train.index.max())

print("\nValidation:")
print(X_val.index.min(), "→", X_val.index.max())

print("\nTest:")
print(X_test.index.min(), "→", X_test.index.max())

# Create Pipeline Setup
pipeline = Pipeline([
    (
        #Applies scaling
        "scaler",
        StandardScaler()
    ),
    (
        #Applies the selection of features based on their MI
        "feature_selection",
        SelectKBest(score_func=mutual_info_classif)
    ),
    (
        #SVM model
        "svm",
        SVC(
            kernel="linear",
            probability=True,
            class_weight="balanced",
            random_state=42,
        )
    )
])

# Hyperparameter Tuning Grid with Values
param_grid = {
    "feature_selection__k": [1, 2, 3, 4, 5, 6, 7, 8, 9, "all"],
    "svm__C":  [0.01, 0.1, 1, 10, 50, 100, 500]
}

# Time-series split logic for cross-validation
tscv = TimeSeriesSplit(n_splits=5)

# GridSearchCV for Selection of Optimal Model
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

#Print the parameters of the best model
print("\nBest Parameters Found:")
print("----------------")
print(grid.best_params_)

# Print Selected Features
selector = best_model.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# Create Predictions using best_model
y_pred = best_model.predict(X_val)

# Print Evaluation Metrics for Validation Set
print("\nValidation SVM Results")
print("-----------------")
print(f"Accuracy : {accuracy_score(y_val, y_pred):.4f}")
print(f"Precision: {precision_score(y_val, y_pred):.4f}")
print(f"Recall   : {recall_score(y_val, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_val, y_pred):.4f}")

# Print Classification Report for Validation Set
print("\nValidation Classification Report:")
print(classification_report(y_val, y_pred))

# Save the optimized model into a pkl file to be loaded
joblib.dump(best_model, "svm.pkl")
