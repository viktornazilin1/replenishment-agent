from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from app.hana_data_loader import load_data_from_hana
from app.forecasting import run_forecast_logic
from app.training_data import build_training_dataset
import os

app = Flask(__name__, static_folder="../static", static_url_path="/")
CORS(app)

# 📦 Главная страница (frontend)
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# 📦 Справочник товаров
@app.route("/api/materials")
def api_materials():
    _, _, materials, _, _, _ = load_data_from_hana()
    materials["material_id"] = materials["material_id"].astype(str)
    return jsonify(materials.to_dict(orient="records"))

# 📦 Справочник магазинов
@app.route("/api/stores")
def api_stores():
    _, _, _, stores, _, _ = load_data_from_hana()
    stores["store_id"] = stores["store_id"].astype(str)
    return jsonify(stores.to_dict(orient="records"))

# 🔮 Прогноз на основе XGBoost
@app.route("/api/forecast", methods=["POST"])
def forecast():
    try:
        data = request.json
        material_id = data.get("material_id")
        store_id = data.get("store_id")
        analysis_type = data.get("analysis_type", "XGBoost")  # теперь всегда XGBoost

        sales, inventory, materials, stores, holidays, promotions = load_data_from_hana()

        result = run_forecast_logic(
            material_id=material_id,
            store_id=store_id,
            analysis_type=analysis_type,
            sales=sales,
            inventory=inventory,
            stores=stores,
            holidays=holidays,
            promotions=promotions
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🧠 Получить обучающий датасет (опционально)
@app.route("/api/training-data")
def training_data():
    try:
        df = build_training_dataset()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚀 Локальный запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
