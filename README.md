COS60016: Programming for Development<br>
Assignment 2: Build a chatbot<br>
24/03/2025<br>
<br>
Flask API prototype integrating OpenWeather API to provide location-based weather data for a blogger's itinerary<br>
<br>
**------- IMPROTANT -------**<br>
API_KEY's required ; located within .env file<br>
https://developers.amadeus.com/ ; AMADEUS_API_KEY & AMADEUS_API_SECRET<br>
https://openweathermap.org/ ; WEATHER_API_KEY<br>
<br>
------- USAGE -------<br>
Use the following keywords to retrieve specific information:<br>
weather – Today’s weather<br>
forecast – 5-day weather forecast<br>
location – Activities and recommendations for the selected location<br>
<br>
------- TESTING -------<br>
The following was used to test the chatbot<br>
<br>
Test Weather<br>
weather bristol<br>
weather Norwich & Bristol & The cotswolds<br>
weather Norwich & oxford & The Cotswolds<br>
weather Melbourne <- Not in the list<br>
<br>
Test Forecasts<br>
forecast Norwich & Bristol & The Cotswolds<br>
forecast Norwich & oxford & The Cotswolds<br>
forecast Sydney <- Not in the list<br>
<br>
Test Amadeus Travel<br>
travel Cambridge & oxford<br>
things to do in oxford & norwich<br>
travel oxford<br>
<br>
Test Chatbot<br>
Hi<br>
tell joke<br>
show Melbourne<br>
<br>
Test Manual Responses<br>
Hello<br>
Tell me a joke<br>
Author<br>
Goodbye<br>
