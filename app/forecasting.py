import pandas as pd
import joblib
import numpy as np
import os
from datetime import timedelta
from app.weather_api import get_weather_forecast_by_coords


model_path = os.path.join(os.path.dirname(__file__), "..", "docker", "xgb_model.joblib")
try:
    xgb_model = joblib.load(model_path)
except Exception as e:
    xgb_model = None
    print("❌ Ошибка загрузки модели:", e)

def to_serializable_dict(d):
    def convert(v):
        if isinstance(v, (np.generic, np.bool_)):
            return v.item()
        if isinstance(v, dict):
            return to_serializable_dict(v)
        return v
    return {k: convert(v) for k, v in d.items()}

def run_forecast_logic(material_id, store_id, analysis_type,
                       sales, inventory, stores, holidays, promotions,
                       weather_api_key="6455196a35377fe0b66c120ff16bd265",
                       forecast_days=7):

    debug_log = {}
    data_used = {
        "weather_used": False,
        "holidays_used": False,
        "promotions_used": False
    }

    # Приведение типов
    for df in [sales, inventory]:
        df["store_id"] = df["store_id"].astype(str)
        df["material_id"] = df["material_id"].astype(str)

    store_row = stores[stores["store_id"] == store_id].iloc[0]
    latitude = float(store_row["latitude"])
    longitude = float(store_row["longitude"])
    city = store_row["city"]
    store_region = store_row.get("state_code", "BE")

    filtered_sales = sales[(sales["material_id"] == material_id) & (sales["store_id"] == store_id)]
    filtered_sales = filtered_sales.groupby("date")["quantity"].sum().reset_index()
    filtered_sales.columns = ["ds", "y"]
    filtered_sales["ds"] = pd.to_datetime(filtered_sales["ds"], errors="coerce")

    debug_log["filtered_sales_rows"] = len(filtered_sales)

    if len(filtered_sales.dropna()) < 2:
        avg_qty = filtered_sales["y"].mean() if len(filtered_sales) > 0 else 0
        fallback_demand = int(avg_qty * forecast_days)
        return to_serializable_dict({
            "predicted_demand": fallback_demand,
            "current_stock": 0,
            "suggested_qty": fallback_demand,
            "has_shortage": True,
            "model_used": False,
            "debug": debug_log,
            "data_used": data_used
        })

    merged = filtered_sales.copy()

    if analysis_type in ["Спрос + Погода", "Спрос + Погода + Праздники + Промо"]:
        weather = get_weather_forecast_by_coords(latitude, longitude, weather_api_key)
        if weather:
            weather_df = pd.DataFrame([{
                "ds": date, "temperature": data["temperature"], "rain": data["rain"]
            } for date, data in weather.items()])
        else:
            fallback_dates = pd.date_range(filtered_sales["ds"].min(), periods=forecast_days + 3)
            weather_df = pd.DataFrame({
                "ds": fallback_dates,
                "temperature": [18.0] * len(fallback_dates),
                "rain": [0.0] * len(fallback_dates)
            })
        weather_df["ds"] = pd.to_datetime(weather_df["ds"], errors="coerce")
        merged = pd.merge(merged, weather_df, on="ds", how="left")
        data_used["weather_used"] = True

    if analysis_type == "Спрос + Погода + Праздники + Промо":
        regional_holidays = holidays[holidays["state_code"] == store_region].copy()
        regional_holidays["pre_holiday"] = regional_holidays["date"] - pd.Timedelta(days=1)

        holiday_flags = pd.DataFrame({
            "ds": pd.date_range(filtered_sales["ds"].min(), periods=forecast_days + 10)
        })
        holiday_flags["is_holiday"] = holiday_flags["ds"].isin(regional_holidays["date"]).astype(int)
        holiday_flags["is_preholiday"] = holiday_flags["ds"].isin(regional_holidays["pre_holiday"]).astype(int)

        merged = pd.merge(merged, holiday_flags, on="ds", how="left")
        data_used["holidays_used"] = True

        promo_filtered = promotions[promotions["material_id"] == material_id].rename(columns={"date": "ds"})
        promo_filtered["ds"] = pd.to_datetime(promo_filtered["ds"], errors="coerce")
        merged = pd.merge(merged, promo_filtered, on="ds", how="left")
        merged["discount_percent"] = merged["discount_percent"].fillna(0)
        data_used["promotions_used"] = True
    else:
        merged["is_holiday"] = 0
        merged["is_preholiday"] = 0
        merged["discount_percent"] = 0

    merged["ds"] = pd.to_datetime(merged["ds"])
    merged["dow"] = merged["ds"].dt.dayofweek
    for i in range(7):
        merged[f"dow_{i}"] = (merged["dow"] == i).astype(int)

    for col in ["temperature", "rain", "is_holiday", "is_preholiday", "discount_percent"] + [f"dow_{i}" for i in range(7)]:
        if col not in merged.columns:
            merged[col] = 0

    debug_log["merged_rows"] = len(merged)

    X = merged[[
        "temperature", "rain", "is_holiday", "is_preholiday",
        "discount_percent", "dow"
    ]].copy()

    y_pred = xgb_model.predict(X)
    predicted_demand = y_pred[-forecast_days:].sum()

    forecast_df = pd.DataFrame({
        "ds": merged["ds"].tail(forecast_days),
        "yhat": y_pred[-forecast_days:]
    })

    forecast_table_html = forecast_df.to_html(index=False, classes="table table-striped")
    web_path = "/static/xgb_placeholder.png"

    stock_row = inventory[(inventory["store_id"] == store_id) & (inventory["material_id"] == material_id)]
    current_stock = int(stock_row["current_stock"].values[0]) if not stock_row.empty else 0
    suggested_qty = max(0, int(predicted_demand - current_stock))

    return to_serializable_dict({
        "city": city,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "predicted_demand": int(predicted_demand),
        "current_stock": current_stock,
        "suggested_qty": suggested_qty,
        "has_shortage": predicted_demand > current_stock,
        "forecast_table_html": forecast_table_html,
        "plot_path": web_path,
        "model_used": True,
        "debug": debug_log,
        "data_used": data_used
    })
