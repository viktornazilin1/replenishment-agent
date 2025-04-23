import requests
from datetime import datetime

def get_weather_forecast_by_coords(lat, lon, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        res = requests.get(url).json()
        forecast = {}
        for entry in res.get("list", []):
            dt = datetime.fromtimestamp(entry["dt"]).strftime("%Y-%m-%d")
            temp = entry["main"]["temp"]
            rain = entry.get("rain", {}).get("3h", 0)
            forecast[dt] = {
                "temperature": temp,
                "rain": rain
            }
        return forecast
    except Exception as e:
        return {}
