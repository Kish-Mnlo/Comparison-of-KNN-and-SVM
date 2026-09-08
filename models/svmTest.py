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

#Read the csv file
df = pd.read_csv("psei_real_sorted.csv")
print(df.columns.tolist())
print(df.head())

# Build Features (Predictor Values)
df = build_features(df)

# Target Variables
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

# Print the Selected Features
selector = SVMmodel.named_steps["feature_selection"]
selected_support = selector.get_support()
selected_features = X.columns[selected_support]

print("\nSelected Features:")
print("-----------------")
for feature in selected_features:
    print(f"- {feature}")

# Predictions of the Model
y_pred = SVMmodel.predict(X_test)
y_prob = SVMmodel.predict_proba(X_test)[:, 1]

# Print Evaluation Metrics
print("\nFinal Model Results")
print("-------------------")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score : {f1_score(y_test, y_pred):.4f}\n")

# Create Confusion Matrix and Print in Terminal
print("Confusion Matrix")
confumatrix = confusion_matrix(y_test, y_pred)
print(confumatrix)

# Plot SVM Confusion Matrix for Visualization
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

# Print Classification Report
print("Classification Report")
print(classification_report(y_test, y_pred))

# Prediction Results into a Dataframe for printing
results = pd.DataFrame(
    {
        "Actual": y_test.values,
        "Predicted": y_pred,
        "Probability_Up": y_prob,
    },
    index=y_test.index,
)

#Print the last 20 predictions for comparison
print("\nLast 20 Predictions")
print(results.tail(20))
