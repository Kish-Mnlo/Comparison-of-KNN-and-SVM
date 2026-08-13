from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
from features3 import build_features

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://comparison-of-knn-and-svm.onrender.com"
])

# Load the model
KNNmodel = joblib.load("knn.pkl")
SVMmodel = joblib.load("svm.pkl")

raw_df = pd.read_csv("psei_data.csv")

raw_df["Date"] = pd.to_datetime(raw_df["Date"])


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

    if not date:
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

@app.route("/admin/update-data", methods=["POST"])
def update_data():

    if "file" not in request.files:
        return jsonify({
            "error": "No CSV file was uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file was selected."
        }), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({
            "error": "Only CSV files are allowed."
        }), 400

    try:

        #read uploaded csv
        uploaded_df = pd.read_csv(file)
        #required columns
        required_columns = [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in uploaded_df.columns
        ]

        if missing_columns:
            return jsonify({
                "error": f"Missing required columns: {missing_columns}"
            }), 400

        #date convert
        uploaded_df["Date"] = pd.to_datetime(
            uploaded_df["Date"],
            errors="coerce"
        )

        if uploaded_df["Date"].isna().any():
            return jsonify({
                "error": "The uploaded CSV contains invalid dates."
            }), 400

        #combine existing and current
        global raw_df

        combined_df = pd.concat(
            [raw_df, uploaded_df],
            ignore_index=True
        )

        #remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=["Date"],
            keep="last"
        )

        
        #chronological sort
        combined_df = combined_df.sort_values(
            "Date"
        ).reset_index(drop=True)

        
        #save raw dataset
        combined_df.to_csv(
            "psei_data.csv",
            index=False
        )

        # Update the in-memory raw dataset
        raw_df = combined_df

       
        #rebuild featurs
        global df

        feature_df = build_features(
            combined_df.copy()
        )

        feature_df["Date"] = pd.to_datetime(
            feature_df["Date"]
        )

        #features dataset
        feature_df.to_csv(
            "psei_features.csv",
            index=False
        )

        # Update the dataframe used by /search
        df = feature_df

        
        #feedback info
        latest_date = (
            combined_df["Date"]
            .max()
            .strftime("%Y-%m-%d")
        )

        return jsonify({
            "message": "PSEI data updated successfully.",
            "latest_date": latest_date,
            "records": len(combined_df)
        }), 200

    except Exception as error:

        print("CSV update error:", error)

        return jsonify({
            "error": "Failed to update PSEI data."
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")


