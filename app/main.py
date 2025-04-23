from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from app.hana_data_loader import load_data_from_hana
from app.forecasting import run_forecast_logic
from app.training_data import build_training_dataset
from hdbcli import dbapi
from datetime import datetime
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import traceback

load_dotenv()

app = Flask(__name__, static_folder="../static", static_url_path="/")
CORS(app)

# 📦 Главная страница
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

# 💾 Сохранение результата в HANA
def insert_to_hana(result, material_id, store_id):
    conn = dbapi.connect(
        address=os.getenv("HANA_HOST"),
        port=int(os.getenv("HANA_PORT", 443)),
        user=os.getenv("HANA_USER"),
        password=os.getenv("HANA_PASSWORD")
    )
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO FORECAST_RESULTS (
            material_id, store_id, forecast_date,
            predicted_demand, current_stock, suggested_qty, run_timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        material_id,
        store_id,
        datetime.today().date(),
        result.get("predicted_demand"),
        result.get("current_stock"),
        result.get("suggested_qty"),
        datetime.now()
    ))
    conn.commit()
    conn.close()

# 🔮 Прогноз и генерация данных для графика
@app.route("/api/forecast", methods=["POST"])
def forecast():
    try:
        data = request.json
        material_id = data.get("material_id")
        store_id = data.get("store_id")
        analysis_type = data.get("analysis_type", "XGBoost")

        print(f"📩 Запрос прогноза: material_id={material_id}, store_id={store_id}, type={analysis_type}")

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

        insert_to_hana(result, material_id, store_id)

        # результат уже отдается как JSON, интерактивный график строится на frontend (Chart.js)
        print("📤 Отправка результата в UI:", result)
        return jsonify(result)

    except Exception as e:
        print("❌ Ошибка прогноза:", e)
        traceback.print_exc()  # 🔍 Покажет стек ошибки
        return jsonify({"error": str(e)}), 500

# 🧠 Получить обучающий датасет
@app.route("/api/training-data")
def training_data():
    try:
        df = build_training_dataset()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# 📦 Создание заявки на закупку
@app.route("/api/purchase-order", methods=["POST"])
def create_purchase_order():
    try:
        data = request.json
        material_id = data.get("material_id")
        store_id = data.get("store_id")
        qty = int(data.get("qty"))

        if qty <= 0:
            return jsonify({"error": "Количество должно быть положительным."}), 400

        conn = dbapi.connect(
            address=os.getenv("HANA_HOST"),
            port=int(os.getenv("HANA_PORT", 443)),
            user=os.getenv("HANA_USER"),
            password=os.getenv("HANA_PASSWORD")
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO PURCHASE_ORDERS (
                material_id, store_id, quantity, created_at
            ) VALUES (?, ?, ?, ?)
        """, (
            material_id,
            store_id,
            qty,
            datetime.now()
        ))

        conn.commit()
        conn.close()

        return jsonify({"message": "✅ Заявка успешно создана в SAP HANA."})

    except Exception as e:
        print("❌ Ошибка при создании заявки:", e)
        return jsonify({"error": str(e)}), 500


# 🚀 Локальный запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
    
    
