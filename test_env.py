import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print API key
print(f"WEATHER_API_KEY: {os.getenv('WEATHER_API_KEY')}")