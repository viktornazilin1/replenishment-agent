from app.hana_data_loader import load_data_from_hana
from app.forecasting import run_forecast_logic
import pandas as pd
from hdbcli import dbapi
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

analysis_types = [
    "Только спрос",
    "Спрос + Погода",
    "Спрос + Погода + Праздники + Промо"
]

def insert_to_hana(result, material_id, store_id, analysis_type):
    print("🔧 Проверка переменных подключения:")
    print("HANA_HOST:", os.getenv("HANA_HOST"))
    print("HANA_PORT:", os.getenv("HANA_PORT"))
    print("HANA_USER:", os.getenv("HANA_USER"))
    print("HANA_PASSWORD:", "*****" if os.getenv("HANA_PASSWORD") else None)
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

try:
    sales, inventory, materials, stores, holidays, promotions = load_data_from_hana()

    materials["material_id"] = materials["material_id"].astype(str)
    stores["store_id"] = stores["store_id"].astype(str)

    for analysis_type in analysis_types:
        print(f"▶️ Тип анализа: {analysis_type}")

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
                    data_used = result.get("data_used", {})
                    print(f"     📊 Использовано: Погода: {data_used.get("weather_used", False)}, Праздники: {data_used.get("holidays_used", False)}, Промо: {data_used.get("promotions_used", False)}")

                    insert_to_hana(result, material_id, store_id, analysis_type)

                except Exception as e:
                    print(f"  ⚠️ Ошибка прогноза: {e}")

except Exception as e:
    print(f"❌ Глобальная ошибка пайплайна: {e}")
