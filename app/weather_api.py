import requests
from datetime import datetime

def get_user_location():
    try:
        res = requests.get("https://ipinfo.io").json()
        return res["city"], res["region"], res["country"]
    except Exception as e:
        return "Unknown", "Unknown", "Unknown"

def get_weather_forecast(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
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
