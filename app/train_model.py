import pandas as pd
import joblib
from app.training_data import build_training_dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import os
from math import sqrt

def train_and_save_model(model_path="app/xgb_model.joblib"):
    print("📦 Подготовка данных...")
    df = build_training_dataset()

    feature_cols = [
        "temperature", "rain", "is_holiday", "is_preholiday",
        "discount_percent", "dow"
    ]
    X = df[feature_cols]
    y = df["y"]

    print(f"🔢 Количество строк: {len(df)}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🚀 Обучение модели XGBoost...")
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("📊 Оценка качества...")
    y_pred = model.predict(X_test)
    rmse = sqrt(mean_squared_error(y_test, y_pred))
    print(f"✅ RMSE: {rmse:.2f}")

    print(f"💾 Сохранение модели в {model_path}...")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    print("🎉 Модель сохранена успешно.")

if __name__ == "__main__":
    train_and_save_model()
