#execute via prompt
import os
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the API Key
API_KEY = os.getenv("WEATHER_API_KEY")

# Debugging output
print(f"DEBUG: WEATHER_API_KEY = {API_KEY}")  # Check if API key is loaded

LAT, LON = 51.4545, -2.5879  # Bristol coordinates
URL = "http://api.openweathermap.org/data/2.5/forecast"

params = {"lat": LAT, "lon": LON, "appid": API_KEY, "units": "metric"}
response = requests.get(URL, params=params)

print("Status Code:", response.status_code)
print("Response:", response.json())
