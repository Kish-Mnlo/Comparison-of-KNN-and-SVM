from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
from features3 import build_features
from datetime import datetime
import yfinance as yf

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://comparison-of-knn-and-svm.onrender.com"
])

# Load the model
KNNmodel = joblib.load("knn.pkl")
SVMmodel = joblib.load("finalsvm.pkl")


def re_update_data():
    global df, last_updated, date
    # Download the df till present time once when the app starts
    ticker = "PSEI.PS"
    df = yf.download(
        ticker,
        start="2016-01-01",
        auto_adjust=True,
        progress=False
    )

    df.index = pd.to_datetime(df.index)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = build_features(df)



    last_updated = datetime.now().date()
    

re_update_data()


@app.route("/search", methods=["POST"])
def search():
    if last_updated != datetime.now().date():
        re_update_data()
    
    caughtdata = request.get_json()

    if not caughtdata:
        return jsonify({
            "error": "No data found.",
            "message": "Please select a date from the calendar."
        }), 400

    date = caughtdata["stock_date"]

    if not date:
        return jsonify({
            "error": "Stock date is required.",
            "message": "Please select a date from the calendar."
        }), 400

    selected_date = pd.to_datetime(date)

    # Find the matching row
    if selected_date not in df.index:
        return jsonify({
            "error": "No data found.",
            "message": "There is no OLHCV data for this date, please select a different one."
        }), 404

    current_index = df.index.get_loc(selected_date)

    current_row = df.iloc[current_index]

    # Get the next trading day (next row)
    next_row = None

    if current_index + 1 < len(df):
        next_row = df.iloc[current_index + 1]

    #actual result
    actual = None

    if next_row is not None:
        if next_row["Close"] > current_row["Close"]:
            actual = "Higher"
        else:
            actual = "Lower"

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
    

    #knn prediction

    knn_prediction_num = KNNmodel.predict(date_feature)[0]
    knn_probability = KNNmodel.predict_proba(date_feature)[0]

    knn_prediction = (
        "Higher" if knn_prediction_num == 1 else "Lower"
    )


    #svm prediction

    svm_prediction_num = SVMmodel.predict(date_feature)[0]
    svm_probability = SVMmodel.predict_proba(date_feature)[0]

    svm_prediction = (
        "Higher" if svm_prediction_num == 1 else "Lower"
    )

    data = {
        "Date": current_row.name.strftime("%Y-%m-%d"),
        "Open": float(current_row["Open"]),
        "High": float(current_row["High"]),
        "Low": float(current_row["Low"]),
        "Close": float(current_row["Close"]),
        "Volume": int(current_row["Volume"]),
    }
    next_data = None if next_row is None else {
        "Date": next_row.name.strftime("%Y-%m-%d"),
        "Open": float(next_row["Open"]),
        "High": float(next_row["High"]),
        "Low": float(next_row["Low"]),
        "Close": float(next_row["Close"]),
        "Volume": int(next_row["Volume"]),
    }
    results = {
    "KNN": {
        "Prediction": knn_prediction,
        "Probability_Higher": f"{knn_probability[1]:.2%}",
        "Probability_Lower": f"{knn_probability[0]:.2%}"
    },
    "SVM": {
        "Prediction": svm_prediction,
        "Probability_Higher": f"{svm_probability[1]:.2%}",
        "Probability_Lower": f"{svm_probability[0]:.2%}"
    }
}

    return jsonify({
        "data": data,
        "next_data": next_data,
        "actual": actual,
        "results": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")