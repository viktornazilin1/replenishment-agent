import pandas as pd
import joblib
import numpy as np
import os
import shutil
from app.weather_api import get_weather_forecast

# Загрузка XGBoost модели
try:
    xgb_model = joblib.load("xgb_model.joblib")
except Exception as e:
    xgb_model = None
    print("❌ Ошибка загрузки модели:", e)


def run_forecast_logic(material_id, store_id, analysis_type,
                       sales, inventory, stores, holidays, promotions,
                       weather_api_key="6455196a35377fe0b66c120ff16bd265",
                       forecast_days=7):

    debug_log = {}

    sales["store_id"] = sales["store_id"].astype(str)
    sales["material_id"] = sales["material_id"].astype(str)
    inventory["store_id"] = inventory["store_id"].astype(str)
    inventory["material_id"] = inventory["material_id"].astype(str)

    store_row = stores[stores["store_id"] == store_id].iloc[0]
    latitude = store_row["latitude"]
    longitude = store_row["longitude"]
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
        return {
            "error": "Недостаточно данных для прогноза.",
            "predicted_demand": fallback_demand,
            "current_stock": 0,
            "suggested_qty": fallback_demand,
            "has_shortage": True,
            "model_used": False,
            "debug": debug_log
        }

    weather = get_weather_forecast(city, weather_api_key)
    if weather:
        weather_df = pd.DataFrame([
            {"ds": date, "temperature": data["temperature"], "rain": data["rain"]}
            for date, data in weather.items()
        ])
        weather_df["ds"] = pd.to_datetime(weather_df["ds"], errors="coerce")
    else:
        fallback_dates = pd.date_range(
            start=filtered_sales["ds"].min(),
            end=filtered_sales["ds"].max() + pd.Timedelta(days=forecast_days + 3)
        )
        weather_df = pd.DataFrame({
            "ds": fallback_dates,
            "temperature": [18.0] * len(fallback_dates),
            "rain": [0.0] * len(fallback_dates)
        })

    regional_holidays = holidays[holidays["state_code"] == store_region].copy()
    regional_holidays["pre_holiday"] = regional_holidays["date"] - pd.Timedelta(days=1)
    holiday_flags = pd.DataFrame({
        "ds": pd.date_range(
            filtered_sales["ds"].min(),
            filtered_sales["ds"].max() + pd.Timedelta(days=forecast_days)
        )
    })
    holiday_flags["is_holiday"] = holiday_flags["ds"].isin(regional_holidays["date"]).astype(int)
    holiday_flags["is_preholiday"] = holiday_flags["ds"].isin(regional_holidays["pre_holiday"]).astype(int)

    merged = filtered_sales.copy()
    merged = pd.merge(merged, weather_df, on="ds", how="left")
    merged = pd.merge(merged, holiday_flags, on="ds", how="left")

    merged["dow"] = merged["ds"].dt.dayofweek
    dow_dummies = pd.get_dummies(merged["dow"], prefix="dow")
    merged = pd.concat([merged, dow_dummies], axis=1)

    promo_filtered = promotions[promotions["material_id"] == material_id].rename(columns={"date": "ds"})
    promo_filtered["ds"] = pd.to_datetime(promo_filtered["ds"], errors="coerce")
    merged = pd.merge(merged, promo_filtered, on="ds", how="left")
    merged["discount_percent"] = merged["discount_percent"].fillna(0)

    cols_to_fill = ["temperature", "rain", "is_holiday", "is_preholiday", "discount_percent"] + [f"dow_{i}" for i in range(7)]
    for col in cols_to_fill:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    debug_log["merged_rows"] = len(merged)

    if len(merged.dropna()) < 2:
        avg_qty = filtered_sales["y"].mean() if len(filtered_sales) > 0 else 0
        fallback_demand = int(avg_qty * forecast_days)
        return {
            "warning": "Недостаточно данных после объединения факторов. Использован fallback.",
            "predicted_demand": fallback_demand,
            "current_stock": 0,
            "suggested_qty": fallback_demand,
            "has_shortage": True,
            "model_used": False,
            "debug": debug_log
        }

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
    web_path = "/static/xgb_placeholder.png"  # Можно заменить на график

    stock_row = inventory[(inventory["store_id"] == store_id) & (inventory["material_id"] == material_id)]
    current_stock = int(stock_row["current_stock"].values[0]) if not stock_row.empty else 0
    suggested_qty = max(0, int(predicted_demand - current_stock))

    return {
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "predicted_demand": int(predicted_demand),
        "current_stock": current_stock,
        "suggested_qty": suggested_qty,
        "has_shortage": predicted_demand > current_stock,
        "forecast_table_html": forecast_table_html,
        "plot_path": web_path,
        "model_used": True,
        "debug": debug_log
    }