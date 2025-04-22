from app.hana_data_loader import load_data_from_hana
from app.forecasting import run_forecast_logic
import pandas as pd
from hdbcli import dbapi
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

analysis_type = "XGBoost"

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

print(f"🚀 Старт batch-пайплайна в SAP AI Core (анализ по всем товарам и магазинам)")
print(f"▶️ Тип анализа: {analysis_type}")

try:
    # Загружаем все таблицы
    sales, inventory, materials, stores, holidays, promotions = load_data_from_hana()

    materials["material_id"] = materials["material_id"].astype(str)
    stores["store_id"] = stores["store_id"].astype(str)

    for material_row in materials.to_dict(orient="records"):
        for store_row in stores.to_dict(orient="records"):
            material_id = material_row["material_id"]
            store_id = store_row["store_id"]

            print(f"\n📦 Анализ: {material_row['description']} / {store_row['store_name']}")

            try:
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
                
                print(f"  🔮 Прогноз: {result.get('predicted_demand')} | Остаток: {result.get('current_stock')} | Пополнить: {result.get('suggested_qty')}")
                insert_to_hana(result, material_id, store_id)

            except Exception as e:
                print(f"  ⚠️ Ошибка прогноза: {e}")

except Exception as e:
    print(f"❌ Глобальная ошибка пайплайна: {e}")
