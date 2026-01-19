#Import Necessary Libraries
from dotenv import load_dotenv # To load environment variables from .env file
import os # To access environment variables
from flask import Flask, render_template, request

load_dotenv()  # Load environment variables from .env file

# Load API keys from environment variables
TICKETMASTER_CONSUMER_KEY = os.getenv("TICKETMASTER_CONSUMER_KEY")
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
EVENTBRITE_API_KEY = os.getenv("EVENTBRITE_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# Import Python Requests Library for use in API calls
import requests

# Function to get events from Ticketmaster API
def get_ticketmaster_events(city):
    url = f"https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TICKETMASTER_CONSUMER_KEY,
        "city": city,
        "size": 12  # Number of events to return
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        events = data.get("_embedded", {}).get("events", [])
        result = []
        for event in events:
            name = event.get("name")
            date = event.get("dates", {}).get("start", {}).get("localDate")
            result.append(f"{name} on {date}")
        return result if result else ["No events found."]
    else:
        return ["Error fetching events."]
    
# Function to get places from Foursquare API
def get_foursquare_places(city, query="restaurant"):
    url = "https://api.foursquare.com/v3/places/search"
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    params = {
        "near": city,
        "query": query,
        "limit": 15
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        places = data.get("results", [])
        result = []
        for place in places:
            name = place.get("name")
            address = ", ".join(place.get("location", {}).get("formatted_address", []))
            result.append(f"{name} - {address}")
        return result if result else ["No places found."]
    else:
        return ["Error fetching places."]
    
# Function to get events from Eventbrite API
def get_eventbrite_events(city):
    url = "https://www.eventbriteapi.com/v3/events/search/"
    headers = {
        "Authorization": f"Bearer {EVENTBRITE_API_KEY}"
    }
    params = {
        "location.address": city,
        "sort_by": "date",
        "page_size": 3
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        events = data.get("events", [])
        result = []
        for event in events:
            name = event.get("name", {}).get("text")
            start = event.get("start", {}).get("local")
            result.append(f"{name} on {start}")
        return result if result else ["No events found."]
    else:
        return ["Error fetching Eventbrite events."]
    
# Function to get places from Geoapify API
def get_geoapify_places(city, category="tourism.sights"):
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "filter": f"place:city:{city}",
        "limit": 3,
        "apiKey": GEOAPIFY_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        places = data.get("features", [])
        result = []
        for place in places:
            name = place.get("properties", {}).get("name")
            address = place.get("properties", {}).get("formatted")
            result.append(f"{name} - {address}")
        return result if result else ["No places found."]
    else:
        return ["Error fetching Geoapify places."]

# Creating Flask App
app = Flask(__name__)

# Simple Bot Logic Function (def): take user input and return a response
def get_bot_response(user_input):
    user_input_lower = user_input.lower()
    if "events in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        events = get_ticketmaster_events(city)
        return "Here are some upcoming events:\n" + "\n".join(events)
    elif "food in" in user_input_lower or "restaurants in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        places = get_foursquare_places(city)
        return "Here are some places to eat:\n" + "\n".join(places)
    elif "eventbrite in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        events = get_eventbrite_events(city)
        return "Here are some Eventbrite events:\n" + "\n".join(events)
    elif "sights in" in user_input_lower or "tourist in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        places = get_geoapify_places(city)
        return "Here are some sights to see:\n" + "\n".join(places)
    elif "hello" in user_input_lower:
        return "Hello! How can I help you today?"
    elif "joke" in user_input_lower:
        return "Why did the computer show up at work late? It had a hard drive!"
    else:
        return f"You said: {user_input}"

# Route for Chat Interface
# 1. When someone visits the root URL ("/"), show them the chat interface.
# 2. If they submit a message (POST request), get the bot response and display it.
@app.route("/", methods=["GET", "POST"])
# 3. Create chat function to handle requests and responses using the chat.html template.
def chat():
    bot_response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        bot_response = get_bot_response(user_input)
    return render_template("chat.html", bot_response=bot_response)

# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)