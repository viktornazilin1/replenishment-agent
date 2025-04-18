
from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

model = joblib.load("xgb_model.joblib")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    X = pd.DataFrame(data)
    preds = model.predict(X)
    return jsonify({"prediction": preds.tolist()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
