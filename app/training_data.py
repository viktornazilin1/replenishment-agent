import pandas as pd
from app.hana_data_loader import load_data_from_hana

def build_training_dataset(forecast_days=7):
    # Загружаем данные
    sales, inventory, materials, stores, holidays, promotions = load_data_from_hana()

    # Приведение типов
    sales["material_id"] = sales["material_id"].astype(str)
    sales["store_id"] = sales["store_id"].astype(str)
    promotions["material_id"] = promotions["material_id"].astype(str)
    promotions["date"] = pd.to_datetime(promotions["date"])
    stores["store_id"] = stores["store_id"].astype(str)

    # Группировка продаж по дням
    grouped = sales.groupby(["store_id", "material_id", "date"])["quantity"].sum().reset_index()
    grouped["date"] = pd.to_datetime(grouped["date"])

    # Признаки: день недели
    grouped["dow"] = grouped["date"].dt.dayofweek

    # Признаки: праздники
    holidays["date"] = pd.to_datetime(holidays["date"])
    holidays["pre_holiday"] = holidays["date"] - pd.Timedelta(days=1)

    # Обогащение по праздникам (для каждого магазина по региону)
    merged = pd.merge(grouped, stores[["store_id", "state_code"]], on="store_id", how="left")

    merged["is_holiday"] = merged.apply(
        lambda row: int(row["date"] in holidays[holidays["state_code"] == row["state_code"]]["date"].values),
        axis=1
    )
    merged["is_preholiday"] = merged.apply(
        lambda row: int(row["date"] in holidays[holidays["state_code"] == row["state_code"]]["pre_holiday"].values),
        axis=1
    )

    # Промо-акции
    promotions["material_id"] = promotions["material_id"].astype(str)
    promotions["date"] = pd.to_datetime(promotions["date"])
    promo = promotions.rename(columns={"date": "promo_date"})
    merged = pd.merge(
        merged,
        promo,
        left_on=["material_id", "date"],
        right_on=["material_id", "promo_date"],
        how="left"
    )
    merged["discount_percent"] = merged["discount_percent"].fillna(0)
    merged.drop(columns=["promo_date"], inplace=True)
  

    # Погода (гео → API уже у тебя есть отдельно, тут заглушка)
    # Можно встроить вызов get_weather_forecast(...) для каждого уникального города → оптимизация позже
    merged["temperature"] = 18.0
    merged["rain"] = 0.0

    # Итоговый вид
    dataset = merged[[
        "store_id", "material_id", "date", "quantity", "temperature", "rain",
        "is_holiday", "is_preholiday", "discount_percent", "dow"
    ]].copy()

    dataset.rename(columns={"date": "ds", "quantity": "y"}, inplace=True)

    return dataset