import subprocess  # Allows execution of system commands, used here to install missing packages dynamically
import sys  # Provides access to system-specific parameters and functions

"""
# Function to install missing packages
def install_package(package):
    # Installs a Python package using pip.
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")

# Install required packages
install_package("flask[async]")
install_package("pandas")
install_package("aiohttp")
install_package("amadeus")
install_package("chatterbot")
install_package("chatterbot_corpus")
install_package("flask_caching")
install_package("spacy")
install_package("pyyaml")
install_package("openpyxl")
install_package("python-dotenv")
"""

import os  # Provides functions for interacting with the operating system.
import multiprocessing  # Enables parallel processing to improve performance in multi-core CPUs
import logging  # Enables logging for debugging and tracking errors
import asyncio  # Provides asynchronous I/O support for concurrent programming
from functools import lru_cache  # Implements caching to speed up function calls with repetitive input
from flask import Flask, render_template, request, jsonify  # Flask framework for creating a web server
import pandas as pd  # Used to read and manipulate data
import aiohttp  # Provides asynchronous HTTP client capabilities (used for API calls)
from concurrent.futures import ThreadPoolExecutor  # Helps run blocking functions in separate threads
from amadeus import Client, ResponseError  # Client for interacting with Amadeus Travel APIs, ResponseError for error handling
from chatterbot import ChatBot  # Provides chatbot functionality
from chatterbot.trainers import ChatterBotCorpusTrainer  # Trainer for training chatbot on predefined data
from flask_caching import Cache  # Implements caching to store API results and reduce redundant calls

# Set multiprocessing method for Windows and Unix
if __name__ == "__main__":
    if sys.platform == "win32":
        multiprocessing.set_start_method("spawn", force=True)
    else:
        multiprocessing.set_start_method("fork", force=True)

app = Flask(__name__)

# Configure Flask-Caching (caching weather & forecasts)
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 600  # Cache expiration set to 10 minutes
cache = Cache(app)

# Initialise ChatterBot
chatbot = ChatBot(
    "BasicBot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="sqlite:///database.sqlite3",
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': "I'm sorry, I don't understand. Can you rephrase?",
            'maximum_similarity_threshold': 0.75
        }
    ]
)

trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

# Load Manual responses
@lru_cache(maxsize=1)
def load_manual_responses() -> dict:
    try:
        df = pd.read_excel("manual_conversations.xlsx", engine="openpyxl")
        return {row["User Input"].strip().lower(): row["Bot Response"] for _, row in df.iterrows()}
    except Exception as e:
        logging.error(f"Error loading chatbot responses: {e}")
        return {}

MANUAL_RESPONSES = load_manual_responses()

# OpenWeatherMap API setup
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Use environment variable for security

CURRENT_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

LOCATIONS = {
    "Cumbria": (54.4609, -3.0886),
    "Corfe Castle": (50.6395, -2.0566),
    "The Cotswolds": (51.8330, -1.8433),
    "Cambridge": (52.2053, 0.1218),
    "Bristol": (51.4545, -2.5879),
    "Oxford": (51.7520, -1.2577),
    "Norwich": (52.6309, 1.2974),
    "Stonehenge": (51.1789, -1.8262),
    "Watergate Bay": (50.4429, -5.0553),
    "Birmingham": (52.4862, -1.8904)
}

# Load weather activity suggestions
@lru_cache(maxsize=1)
def load_weather_activities() -> dict:
    try:
        df = pd.read_excel("weather_activities.xlsx", engine="openpyxl")
        return {row["Weather Condition"].lower(): row["Activities"] for _, row in df.iterrows()}
    except Exception as e:
        print(f"Error loading weather activities: {e}")
        return {}

WEATHER_ACTIVITIES = load_weather_activities()

def generate_activity_links(activities: str, city: str) -> str:
    activity_links = []
    for activity in activities.split(", "):
        search_url = f"https://www.google.com/search?q={activity.replace(' ', '+')}+near+{city.replace(' ', '+')}"
        activity_links.append(f'<a href="{search_url}" target="_blank">{activity}</a>')
    return ", ".join(activity_links)

async def fetch_weather(session: aiohttp.ClientSession, url: str, params: dict) -> dict:
    async with session.get(url, params=params) as response:
        return await response.json()

async def get_weather_for_location(city: str) -> str:
    cache_key = f"weather_{city.lower()}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return f"(Cached) {cached_response}"

    if city not in LOCATIONS:
        return f"{city}: Weather data unavailable."

    lat, lon = LOCATIONS[city]
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}

    async with aiohttp.ClientSession() as session:
        data = await fetch_weather(session, CURRENT_WEATHER_URL, params)

    if "main" in data:
        temp = data["main"].get("temp", "N/A")
        description = data["weather"][0].get("description", "N/A")
        activities = WEATHER_ACTIVITIES.get(description.lower(), "No suggested activities available.")
        activity_links = generate_activity_links(activities,
                                                 city) if activities != "No suggested activities available." else activities

        weather_response = f"<strong style='color:black;'>{city}:</strong><br>Temperature: {temp}°C<br>Condition: {description}<br>Suggested Activities: {activity_links}<br>"
        cache.set(cache_key, weather_response, timeout=600)
        return weather_response
    return f"{city}: Unable to retrieve weather."

async def get_forecast_for_location(city: str) -> str:
    cache_key = f"forecast_{city.lower()}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return f"(Cached) {cached_response}"

    if city not in LOCATIONS:
        return f"{city}: Forecast data unavailable."

    lat, lon = LOCATIONS[city]
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}

    async with aiohttp.ClientSession() as session:
        data = await fetch_weather(session, FORECAST_URL, params)

    if "list" in data:
        daily_forecast = {}
        for forecast in data["list"]:
            date = forecast["dt_txt"].split(" ")[0]
            if date not in daily_forecast:
                temp = forecast["main"].get("temp", "N/A")
                description = forecast["weather"][0].get("description", "N/A")
                activities = WEATHER_ACTIVITIES.get(description.lower(), "No suggested activities available.")
                activity_links = generate_activity_links(activities, city) if activities != "No suggested activities available." else activities
                daily_forecast[date] = f"{date}: {temp}°C, {description}<br>Suggested Activities: {activity_links}"
            if len(daily_forecast) == 5:
                break

        forecast_response = f"<strong style='color:black;'>{city} 5-Day Forecast:</strong><br>" + "<br>".join(daily_forecast.values())
        cache.set(cache_key, forecast_response, timeout=600)
        return forecast_response
    return f"{city}: Unable to retrieve forecast."

# Load environment variables from .env file (if used)
from dotenv import load_dotenv
load_dotenv()

# Initialise Amadeus API Client securely
amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)

async def fetch_amadeus_suggestions(city: str):
    """Fetch travel activity recommendations for a city."""
    try:
        response = amadeus.reference_data.locations.get(keyword=city, subType="CITY")
        locations = response.data

        if not locations:
            return f"No travel recommendations found for {city}."

        city_code = locations[0]["iataCode"]

        # Fetch travel recommendations (activities in the city)
        activities_response = amadeus.shopping.activities.get(latitude=LOCATIONS[city][0], longitude=LOCATIONS[city][1])

        if activities_response.data:
            activities = [f'<a href="https://www.google.com/search?q={act["name"].replace(" ", "+")}+in+{city}" target="_blank">{act["name"]}</a>'
                          for act in activities_response.data[:5]]  # Limit to 5 activities
            return f"<strong style='color:black;'>Top Activities in {city}:</strong><br>" + "<br>".join(activities)
        else:
            return f"No activities found for {city}."
    except ResponseError as e:
        logging.error(f"Amadeus API error: {e}")
        return f"Error retrieving travel suggestions for {city}."
@app.route("/get_response", methods=["POST"])
async def get_response():
    user_message = request.json.get("message", "").strip().lower()

    manual_responses = load_manual_responses()
    requested_locations = [loc for loc in LOCATIONS.keys() if loc.lower() in user_message]

    # Handle weather requests
    if "weather" in user_message:
        if not requested_locations:
            return jsonify({"response": "Unknown location. Please ask for weather from a valid location."})
        weather_responses = await asyncio.gather(*(get_weather_for_location(loc) for loc in requested_locations))
        return jsonify({"response": "<br>".join(weather_responses)})

    # Handle forecast requests
    if "forecast" in user_message:
        if not requested_locations:
            return jsonify({"response": "Unknown location. Please ask for a forecast from a valid location."})
        forecast_responses = await asyncio.gather(*(get_forecast_for_location(loc) for loc in requested_locations))
        return jsonify({"response": "<br>".join(forecast_responses)})

    # Handle travel suggestions via Amadeus
    if "travel" in user_message or "things to do" in user_message:
        if not requested_locations:
            return jsonify({"response": "Please specify a location to get travel recommendations."})
        travel_suggestions = await asyncio.gather(*(fetch_amadeus_suggestions(loc) for loc in requested_locations))
        return jsonify({"response": "<br>".join(travel_suggestions)})

    # Step 2: Check predefined responses
    if user_message in manual_responses:
        return jsonify({"response": manual_responses[user_message]})

    # Step 3: If no predefined response, send to ChatterBot
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        bot_response = await loop.run_in_executor(executor, chatbot.get_response, user_message)

    return jsonify({"response": f"Bot: {bot_response}"})

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
