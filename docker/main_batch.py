from app.hana_data_loader import load_data_from_hana
from app.forecasting import run_forecast_logic
import pandas as pd

analysis_type = "XGBoost"

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

            except Exception as e:
                print(f"  ⚠️ Ошибка прогноза: {e}")

except Exception as e:
    print(f"❌ Глобальная ошибка пайплайна: {e}")
