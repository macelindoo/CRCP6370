#Import Necessary Libraries
from dotenv import load_dotenv # To load environment variables from .env file
import os # To access environment variables
from flask import Flask, render_template, request

load_dotenv(override=True)  # Load environment variables from .env file

# Load API keys from environment variables
TICKETMASTER_CONSUMER_KEY = os.getenv("TICKETMASTER_CONSUMER_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")


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

# Function to get city coordinates from Geoapify API
def get_city_coordinates(city):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": city,
        "apiKey": GEOAPIFY_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        features = data.get("features", [])
        if features:
            coords = features[0]["geometry"]["coordinates"]
            return coords[0], coords[1]  # lon, lat
    return None, None

# Function to get places from Geoapify API
def get_geoapify_places(city, category="tourism.sights"):
    lon, lat = get_city_coordinates(city)
    if lon is None or lat is None:
        return ["Could not find city coordinates."]
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},80000",  # 80km radius
        "limit": 15,
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
            if name and address: # Only include places with a name and address
                result.append(f"{name} - {address}")
        return result if result else [f"No places found for category '{category}'."]
    else:
        return ["Error fetching Geoapify places."]

# Function to get breweries from Open Brewery DB
def get_breweries(city):
    url = "https://api.openbrewerydb.org/v1/breweries"
    params = {
        "by_city": city,
        "per_page": 15
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        breweries = response.json()
        result = []
        for brewery in breweries:
            name = brewery.get("name")
            address = brewery.get("address_1")
            if name and address:
                result.append(f"{name} - {address}")
        return result if result else ["No breweries found in that city."]
    else:
        return ["Error fetching breweries."]
    
# Function to get recipes from TheMealDB
def get_meal_recipes(ingredient):
    url = "https://www.themealdb.com/api/json/v1/1/filter.php"
    params = {"i": ingredient}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        meals = data.get("meals")
        if meals:
            result = [meal.get("strMeal") for meal in meals[:15]] # Get up to 15 meals
            return result
        else:
            return [f"No recipes found for {ingredient}."]
    else:
        return ["Error fetching recipes."]
    
# Function to get popular movies from TMDb
def get_popular_movies():
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {
        "api_key": TMDB_API_KEY
    }
    response = requests.get(url, params=params) # Use params instead of headers
    if response.status_code == 200:
        data = response.json()
        movies = data.get("results", [])
        # Get the top 15 movie titles
        result = [movie.get("title") for movie in movies[:15]]
        return result if result else ["No popular movies found."]
    else:
        # Add a print statement to see the error from the API
        print("TMDb Error:", response.status_code, response.text)
        return ["Error fetching popular movies."]

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
        # Use Geoapify to find restaurants
        places = get_geoapify_places(city, category="catering.restaurant")
        return "Here are some places to eat:\n" + "\n".join(places)
    elif "sights in" in user_input_lower or "tourist in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        # Use Geoapify to find sights (default category)
        places = get_geoapify_places(city)
        return "Here are some sights to see:\n" + "\n".join(places)
    elif "breweries in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        breweries = get_breweries(city)
        return "Here are some breweries:\n" + "\n".join(breweries)
    elif "recipes for" in user_input_lower:
        ingredient = user_input_lower.split("for")[-1].strip()
        recipes = get_meal_recipes(ingredient)
        return f"Here are some recipes with {ingredient}:\n" + "\n".join(recipes)
    elif "movies in" in user_input_lower: # New combined command
        city = user_input_lower.split("in")[-1].strip()
        
        # Call both API functions
        movies = get_popular_movies()
        theaters = get_geoapify_places(city, category="entertainment.cinema")
        
        # Combine the results into one response
        movies_response = "Here are some popular movies right now:\n" + "\n".join(movies)
        theaters_response = f"\n\nHere are some theaters in {city}:\n" + "\n".join(theaters)
        
        return movies_response + theaters_response
    elif "popular movies" in user_input_lower:
        movies = get_popular_movies()
        return "Here are some popular movies right now:\n" + "\n".join(movies)
    elif "theaters in" in user_input_lower or "cinemas in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        theaters = get_geoapify_places(city, category="entertainment.cinema")
        return "Here are some movie theaters:\n" + "\n".join(theaters)
    elif "hello" in user_input_lower:
        return "Hello! How can I help you today?"
    elif "joke" in user_input_lower:
        return "Why did the computer show up at work late? It had a hard drive!"
    else:
        return f"You said: {user_input}"

# Route for Chat Interface
@app.route("/", methods=["GET", "POST"])
def chat():
    bot_response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        bot_response = get_bot_response(user_input)
    return render_template("chat.html", bot_response=bot_response)

# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)