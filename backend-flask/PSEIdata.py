from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
import os

app = Flask(__name__)
# CORS allows requests from these three frontend origins
CORS(app, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://comparison-of-knn-and-svm.onrender.com"
])

# Load the models to be used
KNNmodel = joblib.load("knn.pkl")
SVMmodel = joblib.load("svm.pkl")

#Reads the dataset to be used for information
def read_csv_data():
    global df
    try: 
        df = pd.read_csv(
            "psei_features.csv",
            index_col=0,
            parse_dates=True
        )
        if df.empty:
            raise ValueError("No data in csv.")
        #Turns the dates column into datetime format
        df.index = pd.to_datetime(df.index)
    except Exception as e:
        print(f"Could not load csv data: {e}")
        raise

#This runs as soon as backend is redeployed
read_csv_data()

#Ensures the backend is working properly
@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "KNN/SVM Stock Prediction API is running."
    })

#Handles the algorithm connection when date is selected
@app.route("/search", methods=["POST"])
def search():

    #Gathers the data sent by the frontend which is the date selected
    caughtdata = request.get_json()

    #Error handling if there is no date but form is submitted
    if not caughtdata:
        return jsonify({
            "error": "No data found.",
            "message": "Please select a date from the calendar."
        }), 400

    #Gets the stock_date variable that the front end throws
    date = caughtdata["stock_date"]

    #If there is no date but form is submitted
    if not date:
        return jsonify({
            "error": "Stock date is required.",
            "message": "Please select a date from the calendar."
        }), 400

    #Reformats the date sent by the frontend into the datetime format
    selected_date = pd.to_datetime(date)

    # If (date) matching row not found in the dataset csv, throws error
    # usually happens with weekends, holidays
    if selected_date not in df.index:
        return jsonify({
            "error": "No data found.",
            "message": "There is no OLHCV data for this date, please select a different one."
        }), 404


    #Finds the position of the given date in the dataset
    current_index = df.index.get_loc(selected_date)

    #Gets all of the information of the row in that date
    current_row = df.iloc[current_index]

    # Sets the next row to none
    next_row = None

    # Get the next trading day (the next available row) if it exists
    if current_index + 1 < len(df):
        next_row = df.iloc[current_index + 1]

    #Sets the actual result to none
    actual = None

    #If there is a next trading day, the actual will be calculated
    if next_row is not None:
        if next_row["Close"] > current_row["Close"]:
            actual = "Higher"
        else:
            actual = "Lower"

    #Feature matrix (predictor values)
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

    # X is the dataframe for features and data_feature returns the dataframe of the data of the selected date
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

    # Creates a dictionary for the data gathered to be returned to the front end to display
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

    #Returns the dictionary created to be read by the frontend
    return jsonify({
        "data": data,
        "next_data": next_data,
        "actual": actual,
        "results": results
    })

# Finds an environment var with the PORT, else use 5000 as port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)