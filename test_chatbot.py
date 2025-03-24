import os
import json
import pytest
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # For extracting text from HTML
from flask import Flask

# Load environment variables
load_dotenv()

# Debugging: Check if API key is loaded
print(f"DEBUG: WEATHER_API_KEY = {os.getenv('WEATHER_API_KEY')}")

# Import your Flask app
from app import app

@pytest.fixture
def client():
    """Setup Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def extract_text(html_content):
    """Extracts text from HTML to match chatbot responses."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text().strip()

# Test Manual Responses
@pytest.mark.parametrize("query, expected", [
    ("Goodbye", "Goodbye! Have a great day!"),
    ("Author", "Steven Domagala wrote this code"),
    ("Tell me a joke", "Why don't skeletons fight each other? Because they don't have the guts!"),
    ("Hello", "Hi there! How can I assist you?"),
    ("Show Melbourne", "Bot: Hi"),
    ("Tell a joke", "Bot: Did you hear the one about the mountain goats in the andes?"),
    ("Hi", "Bot: How are you doing?"),
])
def test_manual_responses(client, query, expected):
    """Test predefined chatbot responses."""
    response = client.post("/get_response", json={"message": query})
    data = json.loads(response.data)
    assert expected in data["response"], f"Expected '{expected}', got '{data['response']}'"

# Test Travel Responses
@pytest.mark.parametrize("query, expected", [
    ("travel Oxford", "Top Activities in Oxford"),
    ("things to do in Oxford & Cambridge", "Top Activities in Cambridge"),
    ("travel Cambridge & Oxford", "Top Activities in Cambridge"),
])
def test_travel_responses(client, query, expected):
    """Test travel-related queries and activity recommendations."""
    response = client.post("/get_response", json={"message": query})
    data = json.loads(response.data)
    extracted_text = extract_text(data["response"])  # Convert HTML to plain text
    assert expected in extracted_text, f"Expected '{expected}', got '{extracted_text}'"

# Test Weather Responses
@pytest.mark.parametrize("query, expected", [
    ("weather Bristol", "Bristol:"),  # Should return Bristol's weather
    ("weather Norwich", "Norwich:"),  # Should return Norwich's weather
])
def test_weather_responses(client, query, expected):
    """Test weather retrieval for multiple locations."""
    response = client.post("/get_response", json={"message": query})
    data = json.loads(response.data)
    extracted_text = extract_text(data["response"])

    # Debugging: Print response in case of failure
    print(f"DEBUG: Weather API Response for '{query}': {extracted_text}")

    assert expected in extracted_text, f"Expected '{expected}', got '{extracted_text}'"

# Test Forecast Responses
@pytest.mark.parametrize("query, expected", [
    ("forecast The Cotswolds", "The Cotswolds 5-Day Forecast:"),  # Checking The Cotswolds
    ("forecast Bristol", "Bristol 5-Day Forecast:"),  # Checking Bristol
    ("forecast Norwich & Bristol", ["Norwich 5-Day Forecast:", "Bristol 5-Day Forecast:"]),  # Multiple locations
])
def test_forecast_responses(client, query, expected):
    """Test weather forecast retrieval for multiple locations."""
    response = client.post("/get_response", json={"message": query})
    data = json.loads(response.data)
    extracted_text = extract_text(data["response"])

    # Debugging: Print response in case of failure
    print(f"DEBUG: Forecast API Response for '{query}': {extracted_text}")

    if isinstance(expected, list):
        # Check if ALL expected substrings exist in response
        for phrase in expected:
            assert phrase in extracted_text, f"Expected '{phrase}' but not found in response: {extracted_text}"
    else:
        assert expected in extracted_text, f"Expected '{expected}', got '{extracted_text}'"
