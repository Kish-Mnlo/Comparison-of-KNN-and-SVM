from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app,
     origins=["https://comparison-of-knn-and-svm.onrender.com"])

# Load the model
KNNmodel = joblib.load("knn.pkl")
SVMmodel = joblib.load("svm.pkl")

# Load the CSV once when the app starts
df = pd.read_csv("psei_features.csv")

df["Date"] = pd.to_datetime(df["Date"])


@app.route("/search", methods=["POST"])
def search():
    caughtdata = request.get_json()

    if not caughtdata:
        return jsonify({
            "error": "No data found."
        }), 400

    date = caughtdata["stock_date"]
    algorithm = caughtdata["algorithm"]

    if not date or not algorithm:
        return jsonify({
            "error": "Stock date or algorithm is required."
        }), 400

    selected_date = pd.to_datetime(date)

    # Find the matching row
    matches = df.index[df["Date"] == selected_date]

    if len(matches) == 0:
        return jsonify({
            "error": "No data found."
        }), 404

    current_index = matches[0]

    current_row = df.iloc[current_index]

    # Get the next trading day (next row)
    next_row = None

    if current_index + 1 < len(df):
        next_row = df.iloc[current_index + 1]

    features = [
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

    X = df[features]
    date_feature = X.iloc[[current_index]]
    

    if algorithm == "KNN":
        model = KNNmodel
    elif algorithm == "SVM":
        model = SVMmodel
    else:
        return jsonify({
            "error": "Invalid algorithm. Choose KNN or SVM."
        }), 400


    prediction_num = model.predict(date_feature)[0]  
    probability = model.predict_proba(date_feature)[0]    

    if prediction_num == 1:
        prediction = "Higher"
    else:
        prediction = "Lower"

    data = {
        "Date": current_row["Date"].strftime("%Y-%m-%d"),
        "Open": float(current_row["Open"]),
        "High": float(current_row["High"]),
        "Low": float(current_row["Low"]),
        "Close": float(current_row["Close"]),
        "Volume": int(current_row["Volume"]),
    }
    next_data = None if next_row is None else {
        "Date": next_row["Date"].strftime("%Y-%m-%d"),
        "Open": float(next_row["Open"]),
        "High": float(next_row["High"]),
        "Low": float(next_row["Low"]),
        "Close": float(next_row["Close"]),
        "Volume": int(next_row["Volume"]),
    }
    results = {
        "Prediction": prediction,
        "Probability_Higher": f"{probability[1]:.2%}",
        "Probability_Lower": f"{probability[0]:.2%}",
        "Algorithm": algorithm
    }

    return jsonify({
        "data": data,
        "next_data": next_data,
        "results": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")


