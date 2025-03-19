import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv  # Ensure environment variables are loaded

# Load API keys from .env
load_dotenv()

# Retrieve API keys
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

# Debugging: Print API Key (ensure it's loaded properly)
print(f"DEBUG: AMADEUS_API_KEY = {AMADEUS_API_KEY}")

# Check if keys are missing
if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
    raise ValueError("ERROR: Amadeus API credentials are missing!")

# Initialise Amadeus API Client
amadeus = Client(
    client_id=AMADEUS_API_KEY,
    client_secret=AMADEUS_API_SECRET
)

# ✅ Define a test function for pytest
def test_amadeus_norwich():
    """Test Amadeus API for Norwich travel activities"""
    try:
        response = amadeus.reference_data.locations.get(keyword="Norwich", subType="CITY")
        print("Norwich API Response:", response.data)
        assert response.data, "No data found for Norwich"
    except ResponseError as e:
        print("Error:", e)
        assert False, f"Amadeus API Error: {e}"
