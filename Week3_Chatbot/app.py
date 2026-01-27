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
# Import random for random selections
import random
# Import personality json for personality traits
import json
#Import re for regex operations so we can match whole words
import re

# Load personality traits from JSON file
with open('personality.json') as f:
    PERSONALITY = json.load(f)

# TMDb Genre Mapping
TMDB_GENRES = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "sci-fi": 878,
    "tv movie": 10770,
    "thriller": 53,
    "war": 10752,
    "western": 37
}

# Function to get movies by genre and year from TMDb
def get_movies_by_genre(genre=None, year=None):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "popularity.desc",
        "page": 1
    }
    if genre and genre in TMDB_GENRES:
        params["with_genres"] = TMDB_GENRES[genre]
    if year:
        params["primary_release_year"] = year
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        movies = data.get("results", [])
        # Return (title, TMDb URL) tuples
        result = [
            (movie.get("title"), f"https://www.themoviedb.org/movie/{movie.get('id')}")
            for movie in movies[:15]
        ]
        return result if result else []
    else:
        print("TMDb Error:", response.status_code, response.text)
        return []

# Function to get book recommendations from Google Books API
def get_book_recommendation(subject="fiction"):
    url = f"https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"subject:{subject}", "maxResults": 10}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            book = random.choice(items)
            info = book.get("volumeInfo", {})
            title = info.get("title", "Unknown Title")
            authors = ", ".join(info.get("authors", [])) if info.get("authors") else "Unknown Author"
            return f"<strong>{title}</strong> by {authors}"
        else:
            return "No books found for that subject."
    else:
        return "Error fetching book recommendations."

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
            url = event.get("url")  # Ticketmaster event page
            if name and url:
                result.append((f"{name} on {date}", url))
        return result if result else []
    else:
        return []

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
def get_geoapify_places(city, category="tourism.sights", radius=80000):
    lon, lat = get_city_coordinates(city)
    if lon is None or lat is None:
        return []
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},{radius}",  # radius in meters
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
            if name and address:
                result.append(f"{name} - {address}")
        return result
    else:
        return []

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
    print("MealDB API:", response.url, response.status_code, response.text)
    if response.status_code == 200: # Successful response
        data = response.json() # Parse JSON response
        meals = data.get("meals") # Get list of meals
        if meals: # If meals found
            return [
                (meal.get("strMeal"), f"https://www.themealdb.com/meal/{meal.get('idMeal')}") # Return (meal name, MealDB URL) tuples
                for meal in meals[:15] # Limit to 15 results
            ]
        else:
            # Fallback: try searching by meal name
            url2 = "https://www.themealdb.com/api/json/v1/1/search.php"
            params2 = {"s": ingredient}
            response2 = requests.get(url2, params=params2)
            print("MealDB Fallback API:", response2.url, response2.status_code, response2.text)
            if response2.status_code == 200:
                data2 = response2.json()
                meals2 = data2.get("meals")
                if meals2:
                    return [
                        (meal.get("strMeal"), f"https://www.themealdb.com/meal/{meal.get('idMeal')}")
                        for meal in meals2[:15]
                    ]
    return []
    
# Function to get popular movies from TMDb
def get_popular_movies():
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {
        "api_key": TMDB_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        movies = data.get("results", [])
        # Return (title, TMDb URL) tuples
        result = [
            (movie.get("title"), f"https://www.themoviedb.org/movie/{movie.get('id')}")
            for movie in movies[:15]
        ]
        return result if result else []
    else:
        print("TMDb Error:", response.status_code, response.text)
        return []

# Creating Flask App
app = Flask(__name__)

# Simple Bot Logic Function (def): take user input and return a response
def get_bot_response(user_input):
    user_input_lower = user_input.lower()

    # Goodbyes
    if any(word in user_input_lower for word in PERSONALITY.get("goodbye_keywords", [])):
        return random.choice(PERSONALITY.get("goodbyes", ["Goodbye!"]))

    # Thanks
    if any(re.search(rf"\b{re.escape(word)}\b", user_input_lower) for word in PERSONALITY.get("thanks_keywords", [])):
        return random.choice(PERSONALITY.get("thanks", ["You're welcome!"]))

    # Greetings (match whole words only)
    bot_name = PERSONALITY.get("bot_name", "Activabot")
    for word in PERSONALITY["greeting_keywords"]:
        if re.search(rf"\b{re.escape(word)}\b", user_input_lower):
            greeting = random.choice(PERSONALITY["greetings"]).replace("{bot_name}", bot_name)
            return greeting

    # Help command
    if "help" in user_input_lower or "directions" in user_input_lower:
        return (
            f"<strong>Welcome to {bot_name}!</strong><br><em>Your fun-seeking, pun-loving activity sidekick!</em><br><br>"
            "I can help you find <b>events</b>, <b>restaurants</b>, <b>breweries</b>, <b>sights</b>, <b>theaters</b>, <b>movies</b>, <b>recipes</b>, and <b>books</b>.<br><br>"
            "<b>How to use me:</b><ul>"
            "<li>events in Dallas</li>"
            "<li>restaurants near 73019</li>"
            "<li>breweries in Austin</li>"
            "<li>sights in Paris, France</li>"
            "<li>theaters in Miami, OK</li>"
            "<li>movies in Houston</li>"
            "<li>action movies from 1995</li>"
            "<li>random movie</li>"
            "<li>recipes for chicken</li>"
            "<li>book about science</li>"
            "</ul>"
            "You can use <b>in</b> or <b>near</b> for city, state, country, or zipcode. If nothing is found, I'll automatically expand the search area!"
        )

    # Flexible restaurant queries (city, state, country, or zipcode)
    elif (
        "where can i eat" in user_input_lower
        or "places to eat" in user_input_lower
        or "good food" in user_input_lower
        or "restaurants near" in user_input_lower
        or "places to eat near" in user_input_lower
        or "restaurants in" in user_input_lower
        or "food in" in user_input_lower
    ):
        match = re.search(r"(?:near|in)\s+([a-zA-Z0-9 ,]+)", user_input_lower)
        if match:
            location = match.group(1).strip()
            # Try default radius first
            places = get_geoapify_places(location, category="catering.restaurant", radius=80000)
            # If no results, try a larger radius
            if not places:
                places = get_geoapify_places(location, category="catering.restaurant", radius=150000)
            if not places:
                return f"No restaurants found near {location}."
            restaurant_links = [
                f'<a href="https://www.google.com/maps/search/{name.split(" - ")[0].replace(" ", "+")}+{location.replace(" ", "+")}" target="_blank">{name}</a>'
                for name in places
            ]
            intro = random.choice(PERSONALITY.get("restaurant_intros", ["Here are some places to eat:"]))
            return f"{intro}<br>" + "<br>".join(restaurant_links)
        else:
            return "Please specify a city, state, country, or zipcode, e.g., 'restaurants in Dallas' or 'places to eat near 75001'."

    # Events
    elif "events in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        events = get_ticketmaster_events(city)
        if not events:
            return f"No events found in {city}."
        event_links = [
            f'<a href="{url}" target="_blank">{name}</a>'
            for name, url in events
        ]
        intro = random.choice(PERSONALITY.get("event_intros", ["Here are some upcoming events:"]))
        return f"{intro}<br>" + "<br>".join(event_links)

    # Restaurants (direct command)
    elif "food in" in user_input_lower or "restaurants in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        places = get_geoapify_places(city, category="catering.restaurant")
        if not places:
            return f"No restaurants found in {city}."
        restaurant_links = [
            f'<a href="https://www.google.com/maps/search/{name.replace(" ", "+")}+{city.replace(" ", "+")}" target="_blank">{name}</a>'
            for name in places
        ]
        intro = random.choice(PERSONALITY.get("restaurant_intros", ["Here are some places to eat:"]))
        return f"{intro}<br>" + "<br>".join(restaurant_links)

    # Sights
    elif (
            "sights" in user_input_lower
            or "tourist" in user_input_lower
        ):
            match = re.search(r"(?:near|in)\s+([a-zA-Z0-9 ,]+)", user_input_lower)
            if match:
                location = match.group(1).strip()
                # Try default radius first
                places = get_geoapify_places(location, category="tourism.sights", radius=80000)
                # If no results, try a larger radius
                if not places:
                    places = get_geoapify_places(location, category="tourism.sights", radius=150000)
                if not places:
                    return f"No sights found near {location}."
                sight_links = [
                    f'<a href="https://www.google.com/maps/search/{name.split(" - ")[0].replace(" ", "+")}+{location.replace(" ", "+")}" target="_blank">{name}</a>'
                    for name in places
                ]
                intro = random.choice(PERSONALITY.get("sight_intros", ["Here are some sights to see:"]))
                return f"{intro}<br>" + "<br>".join(sight_links)
            else:
                return "Please specify a city, state, country, or zipcode, e.g., 'sights in Paris' or 'tourist near 75001'."

    # Breweries
    elif "breweries in" in user_input_lower:
        city = user_input_lower.split("in")[-1].strip()
        breweries = get_breweries(city)
        if not breweries:
            return f"No breweries found in {city}."
        brewery_links = [
            f'<a href="https://www.google.com/maps/search/{name.replace(" ", "+")}+{city.replace(" ", "+")}" target="_blank">{name}</a>'
            for name in breweries
        ]
        intro = random.choice(PERSONALITY.get("brewery_intros", ["Here are some breweries:"]))
        return f"{intro}<br>" + "<br>".join(brewery_links)

    # Recipes
    elif "recipes for" in user_input_lower or "recipes with" in user_input_lower or "recipes using" in user_input_lower:
        match = re.search(r"recipes (?:for|with|using)\s+([a-zA-Z0-9 \-]+)", user_input_lower)
        if match:
            ingredient = match.group(1).strip()
            recipes = get_meal_recipes(ingredient)
            if not recipes:
                return f"No recipes found with {ingredient}."
            recipe_links = [f'<a href="{url}" target="_blank">{name}</a>' for name, url in recipes]
            intro = random.choice(PERSONALITY.get("recipe_intros", ["Here are some recipes:"]))
            return f"{intro}<br>" + "<br>".join(recipe_links)
        else:
            return "Please specify an ingredient, e.g., 'recipes with chicken'."

    # Movies + Theaters (combined)
    # Movies + Theaters (combined)
    elif "movies in" in user_input_lower or "movies near" in user_input_lower:
        if "movies in" in user_input_lower:
            city = user_input_lower.split("in")[-1].strip()
        else:
            city = user_input_lower.split("near")[-1].strip()
        movies = get_popular_movies()
        theaters = get_geoapify_places(city, category="entertainment.cinema")
        # Make movie titles clickable
        movie_links = [f'<a href="{url}" target="_blank">{title}</a>' for title, url in movies]
        # Make theater names clickable (Google Maps search)
        theater_links = [
            f'<a href="https://www.google.com/maps/search/{name.replace(" ", "+")}+{city.replace(" ", "+")}" target="_blank">{name}</a>'
            for name in theaters
        ]
        intro = random.choice(PERSONALITY.get("movie_intros", ["Here are some popular movies right now:"]))
        movies_response = f"{intro}<br>" + "<br>".join(movie_links)
        theaters_response = f"<br><br>Here are some theaters in {city}:<br>" + "<br>".join(theater_links)
        return movies_response + theaters_response

       # Movies by genre, year, decade, or random
    elif "movie" in user_input_lower:
        import random as pyrandom

        # Extract genre
        genre = None
        for g in TMDB_GENRES:
            if g in user_input_lower:
                genre = g
                break

        # Extract year
        year = None
        match_year = re.search(r"\b(19\d{2}|20\d{2})\b", user_input_lower)
        if match_year:
            year = match_year.group(1)

        # Extract decade (e.g., "1980s", "1970s")
        match_decade = re.search(r"\b(19\d0|20\d0)s\b", user_input_lower)
        if match_decade:
            decade_start = int(match_decade.group(1))
            year = str(pyrandom.randint(decade_start, decade_start + 9))

        # Random movie request
        if "random" in user_input_lower:
            # Pick a random year between 1950 and last year
            rand_year = pyrandom.randint(1950, 2025)
            # Pick a random page (TMDb allows up to 500)
            rand_page = pyrandom.randint(1, 10)
            url = "https://api.themoviedb.org/3/discover/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "sort_by": "popularity.desc",
                "page": rand_page,
                "primary_release_year": rand_year
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                movies = data.get("results", [])
                if movies:
                    movie = pyrandom.choice(movies)
                    title = movie.get("title", "Unknown Title")
                    link = f"https://www.themoviedb.org/movie/{movie.get('id')}"
                    return f'Here is a random movie from {rand_year}:<br><a href="{link}" target="_blank">{title}</a>'
                else:
                    return "Couldn't find a random movie right now."
            else:
                return "Error fetching a random movie."
        else:
            movies = get_movies_by_genre(genre, year)
            if not movies:
                return "No movies found for your request."
            movie_links = [f'<a href="{url}" target="_blank">{title}</a>' for title, url in movies]
            if genre and year:
                header = f"Here are some {genre.title()} movies from {year}:<br>"
            elif genre:
                header = f"Here are some {genre.title()} movies:<br>"
            elif year:
                header = f"Here are some movies from {year}:<br>"
            else:
                header = "Here are some popular movies right now:<br>"
            return header + "<br>".join(movie_links)

    # Theaters only
    elif (
            "theaters" in user_input_lower
            or "cinemas" in user_input_lower
        ):
            match = re.search(r"(?:near|in)\s+([a-zA-Z0-9 ,]+)", user_input_lower)
            if match:
                location = match.group(1).strip()
                # Try default radius first
                theaters = get_geoapify_places(location, category="entertainment.cinema", radius=80000)
                # If no results, try a larger radius
                if not theaters:
                    theaters = get_geoapify_places(location, category="entertainment.cinema", radius=150000)
                if not theaters:
                    return f"No theaters found near {location}."
                theater_links = [
                    f'<a href="https://www.google.com/maps/search/{name.split(" - ")[0].replace(" ", "+")}+{location.replace(" ", "+")}" target="_blank">{name}</a>'
                    for name in theaters
                ]
                return f"Here are some movie theaters near {location}:<br>" + "<br>".join(theater_links)
            else:
                return "Please specify a city, state, country, or zipcode, e.g., 'theaters in Dallas' or 'cinemas near 75001'."
    
    # Book recommendations
        # Book recommendations
    elif "book" in user_input_lower or "read" in user_input_lower or "novel" in user_input_lower:
        # Try to extract a subject/genre from the user input, default to fiction
        match = re.search(
            r"(?:book|books|read|novel|recommendation|recommend|show me|suggest)?(?:\s*(?:about|on|for|in|of|regarding|concerning|related to|on the subject of))?\s*([a-zA-Z0-9 \-]+)?",
            user_input_lower
        )
        subject = match.group(1).strip() if match and match.group(1) else "fiction"
        # Clean up subject (remove leading words and numbers)
        subject = re.sub(r"^(a|an|few|some|the|to|me|of|on|about|for|in|show|recommend|suggest|\d+)\s+", "", subject, flags=re.IGNORECASE)
        subject = subject.strip().lower()
        if not subject or subject in ["book", "books", "novel", "recommendation", "recommend", "read"]:
            subject = "fiction"
        url = f"https://www.googleapis.com/books/v1/volumes"
        params = {"q": f"subject:{subject}", "maxResults": 5}
        response = requests.get(url, params=params)
        items = []
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
        # Fallback: try keyword search if subject search fails
        if not items and subject != "fiction":
            params = {"q": subject, "maxResults": 5}
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
        if items:
            books = []
            for book in items:
                info = book.get("volumeInfo", {})
                title = info.get("title", "Unknown Title")
                authors = ", ".join(info.get("authors", [])) if info.get("authors") else "Unknown Author"
                link = info.get("infoLink", "#")
                books.append(f'<a href="{link}" target="_blank"><strong>{title}</strong></a> by {authors}')
            intro = random.choice(PERSONALITY.get("book_intros", ["Here are some books you might like:"]))
            return f"{intro}<br>" + "<br>".join(books)
        else:
            return f"No books found for {subject}."

    # Greetings
    elif "hello" in user_input_lower:
        return "Hello! How can I help you today?"

    # Fallback
    else:
         fallback = random.choice(PERSONALITY["fallbacks"]).replace("{bot_name}", bot_name)
         return fallback

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