#Import Necessary Libraries
from dotenv import load_dotenv # To load environment variables from .env file
import os # To access environment variables
from flask import Flask, render_template, request

# Import Open AI
import openai

# Import Python Requests Library for use in API calls
import requests
# Import random for random selections
import random
# Import personality json for personality traits
import json
#Import re for regex operations so we can match whole words
import re

load_dotenv(override=True)  # Load environment variables from .env file

# Load API keys from environment variables
TICKETMASTER_CONSUMER_KEY = os.getenv("TICKETMASTER_CONSUMER_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
# Test OMDb API key (optional, for debugging)
# url = "http://www.omdbapi.com/"
# params = {"apikey": OMDB_API_KEY, "t": "Inception"}
# response = requests.get(url, params=params)
# print(response.json())


# Load personality traits from JSON file
with open('personality.json') as f:
    PERSONALITY = json.load(f)

import requests
url = "https://v2.jokeapi.dev/joke/Misc,Pun?type=single&safe-mode"
response = requests.get(url, timeout=5)
print(response.status_code)
print(response.json())

import requests
url = "https://www.googleapis.com/books/v1/volumes"
params = {"q": "subject:fiction", "maxResults": 5}
response = requests.get(url, params=params)
print(response.status_code)
print(response.json())

def ask_chatgpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or "gpt-3.5-turbo" if you want a cheaper model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message['content']

import requests
import re

def get_wiki_fact(topic):
    topic_key = topic.lower().replace("_", " ")
    # Get intros for the topic, or default
    intros = PERSONALITY.get("fact_intros", {}).get(topic_key, []) + PERSONALITY.get("fact_intros", {}).get("default", [
        "Here's a fun fact:",
        "Did you know?",
        "Let me hit you with some trivia:",
        "While we're on the subject:"
    ])
    intro = random.choice(intros)
    # Wikipedia API
    topic_api = topic.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic_api}"
    headers = {
        "User-Agent": "Activabot/1.0 (https://yourdomain.com/; contact@example.com)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Wikipedia API URL: {url} | Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            extract = data.get("extract")
            if extract:
                # Split extract into sentences and pick one at random
                sentences = re.split(r'(?<=[.!?]) +', extract)
                fact = random.choice([s for s in sentences if len(s.strip()) > 0])
                return f"{intro} {fact}"
        # Optionally, add your own custom facts for more variety
        custom_facts = PERSONALITY.get("custom_facts", {}).get(topic_key, [])
        if custom_facts:
            return f"{intro} {random.choice(custom_facts)}"
        return ""
    except Exception as e:
        print("Wikipedia API error:", e)
        return ""

def get_random_joke(topic=None):
    # Custom topic jokes
    custom_jokes = {
        "restaurant": [
            "Why did the tomato turn red? Because it saw the salad dressing!",
            "I asked the waiter for the soup of the day. He said, 'Whiskey.'",
        ],
        "book": [
            "Why are books always cold? Because they have so many fans!",
            "I’m reading a book on anti-gravity. It’s impossible to put down!",
        ],
        # Add more topics as needed
    }
    if topic and topic.lower() in custom_jokes:
        return random.choice(custom_jokes[topic.lower()])
    # Fallback to JokeAPI
    url = "https://v2.jokeapi.dev/joke/Misc,Pun?type=single&safe-mode"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            joke = data.get("joke", "No joke found, but I'm still smiling!")
            return joke
    except Exception:
        return "Sorry, my joke generator is on vacation!"

def get_actor_favorite_movie(actor_name):
    # Try to get from your personality.json first
    favorites = PERSONALITY.get("actor_favorites", {})
    if actor_name.lower() in favorites:
        return favorites[actor_name.lower()]
    # Otherwise, fetch from OMDb (or TMDb) dynamically
    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "s": actor_name,
        "type": "movie"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        movies = data.get("Search", [])
        if movies:
            top_movie = movies[0].get("Title", "a movie")
            return f"My favorite {actor_name} movie is {top_movie}!"
    return f"I don't have a favorite {actor_name} movie yet, but I'm always open to suggestions!"

def get_personality_opinion_or_fact(movie_title):
    title_key = movie_title.lower()
    facts = PERSONALITY.get("movie_facts", {})
    opinions = PERSONALITY.get("movie_opinions", {})
    fallbacks = PERSONALITY.get("movie_fallbacks", [])
    fact_intros = PERSONALITY.get("fact_intros", [
        "Here's a tidbit:", "Movie trivia time:", "Did you know?", "Fun fact coming up:",
        "Here's something cool:", "This is one of my top genres:", "Here's a juicy detail:", "Here's a popcorn-worthy fact:"
    ])

    options = []

    # Add all facts (as individual options)
    if title_key in facts:
        fact_list = facts[title_key]
        if isinstance(fact_list, list):
            options.extend([f"{random.choice(fact_intros)} {fact}" for fact in fact_list])
        else:
            options.append(f"{random.choice(fact_intros)} {fact_list}")

    # Add all opinions (as individual options)
    if title_key in opinions:
        opinion_list = opinions[title_key]
        if isinstance(opinion_list, list):
            options.extend([f"My take: {op}" for op in opinion_list])
        else:
            options.append(f"My take: {opinion_list}")

# Function to get personality opinion or fact about a movie
def get_personality_opinion_or_fact(movie_title, movie_year=None):
    title_key = movie_title.lower()
    facts = PERSONALITY.get("movie_facts", {})
    opinions = PERSONALITY.get("movie_opinions", {})
    fallbacks = PERSONALITY.get("movie_fallbacks", [])
    generic_intros = PERSONALITY.get("fact_intros", [
        "Here's a tidbit:", "Movie trivia time:", "Did you know?", "Fun fact coming up:",
        "Here's something cool:", "Here's a juicy detail:", "Here's a popcorn-worthy fact:"
    ])
    omdb_fact_intros = PERSONALITY.get("omdb_fact_intros", {})

    options = []

    # Add all facts (as individual options)
    if title_key in facts:
        fact_list = facts[title_key]
        if isinstance(fact_list, list):
            options.extend([f"{random.choice(generic_intros)} {fact}" for fact in fact_list])
        else:
            options.append(f"{random.choice(generic_intros)} {fact_list}")

    # Add all opinions (as individual options)
    if title_key in opinions:
        opinion_list = opinions[title_key]
        if isinstance(opinion_list, list):
            options.extend([f"My take: {op}" for op in opinion_list])
        else:
            options.append(f"My take: {opinion_list}")

    # Add OMDb fields as fun facts, but SKIP Plot (since it's in the main response)
    data = get_omdb_movie_info(movie_title, movie_year)
    seen_omdb_values = set()
    if data:
        omdb_fields = [
            ("Awards", "Awards"),
            ("BoxOffice", "BoxOffice"),
            ("Production", "Production"),
            ("Genre", "Genre"),
            ("Director", "Director"),
            ("Actors", "Actors"),
            ("Writer", "Writer"),
            ("Country", "Country"),
            ("Language", "Language"),
            ("Released", "Released"),
            ("Runtime", "Runtime"),
        ]
        for field, label in omdb_fields:
            value = data.get(field)
            if value and value != "N/A" and value not in seen_omdb_values:
                intros = omdb_fact_intros.get(label, generic_intros)
                intro = random.choice(intros)
                if not intro.endswith(":"):
                    intro += ":"
                formatted = f"{intro} {value}"
                options.append(formatted)
                seen_omdb_values.add(value)

    if not options and fallbacks:
        options.append(random.choice(fallbacks))

    return random.choice(options) if options else ""

# Function to get movie info from OMDb API
def get_omdb_movie_info(title, year=None):
    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "t": title
    }
    if year:
        params["y"] = year
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return data
        else:
            return None
    else:
        return None

# TMDb Genre Mapping
# number to genre name mapping from TMDb API
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

# Function to get book recs from Open Library API
def get_openlibrary_books(subject="fiction"):
    url = f"https://openlibrary.org/search.json"
    params = {"subject": subject, "limit": 10}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        books = []
        for doc in data.get("docs", []):
            title = doc.get("title")
            author = ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Unknown author"
            year = doc.get("first_publish_year", "N/A")
            books.append(f"<b>{title}</b> by {author} ({year})")
        return books if books else ["No books found for that topic."]
    else:
        return ["Sorry, I couldn't fetch books right now."]

# Function to get book recommendations from Google Books API
def get_book_recommendation(subject="fiction"):
    url = f"https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"subject:{subject}", "maxResults": 10}
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
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            joke = get_random_joke()
            return f"{intro}<br>" + "<br>".join(books) + f"<br><br><i>{joke_intro} {joke}</i>"
        else:
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            return f"No books found for {subject}.<br><br><i>{joke}</i>"

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
        print("Geoapify places:", places)
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

# Function to search for a movie on TMDb    
def search_tmdb_movie(title, year=None):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year:
        params["year"] = year
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        # Try to find an exact title match (case-insensitive)
        exact_matches = [movie for movie in results if movie.get("title", "").lower() == title.lower()]
        if exact_matches:
            # Pick the most recent by release_date
            movie = max(exact_matches, key=lambda m: m.get("release_date", ""))
            return {
                "title": movie.get("title"),
                "year": movie.get("release_date", "")[:4],
                "id": movie.get("id"),
                "url": f"https://www.themoviedb.org/movie/{movie.get('id')}"
            }
        # Fallback: pick the most recent result
        if results:
            movie = max(results, key=lambda m: m.get("release_date", ""))
            return {
                "title": movie.get("title"),
                "year": movie.get("release_date", "")[:4],
                "id": movie.get("id"),
                "url": f"https://www.themoviedb.org/movie/{movie.get('id')}"
            }
    return None

# Creating Flask App
app = Flask(__name__)

# Simple Bot Logic Function (def): take user input and return a response
def get_bot_response(user_input):
    user_input_lower = user_input.lower()

    # If the user is asking for a book, movie, or info, allow all topics
    is_media_query = any(
        kw in user_input_lower
        for kw in ["book", "novel", "read", "movie", "film", "show", "series", "documentary"]
    )
    is_info_query = any(
        kw in user_input_lower
        for kw in ["who is", "what is", "tell me about", "info about", "information about"]
    )

    # Only block if it's a dangerous intent, not a media/info search
    if not (is_media_query or is_info_query):
        dangerous_patterns = [
            r"how to (make|build|create|cook|synthesize|prepare) (a )?(bomb|poison|explosive|weapon|drug|meth|overdose)",
            r"recipe for (poison|explosive|bomb|meth|drugs|overdose)",
            r"best way to (kill|murder|harm|hurt)",
            r"where to buy (bomb|poison|drugs|weapon|explosive)",
            r"how can i (kill|murder|harm|hurt|overdose)"
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, user_input_lower):
                return (
                    "Whoa there! 🚨 I'm all about fun and good vibes, not felonies or foul play. "
                    "How about a recipe for chocolate cake instead? 🍰"
                )

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

    # OMDb movie info intent
    match = re.search(
    r"(?:get info (?:about|for|on)|tell me about|movie info|info (?:about|for|on)|what is|who is)\s+(.+?)(?:[.?!]|$)", user_input_lower
    )
    if match:
        movie_title = match.group(1).strip(" .?!,")
        print(f"OMDb intent triggered. Movie title: '{movie_title}'")  # <-- Add this line
        data = get_omdb_movie_info(movie_title)
        print(f"OMDb API response: {data}")  # <-- And this line
        if data:
            movie_intro = random.choice(PERSONALITY.get("movie_response_intros", [
                "Oh, I love movies! Here’s what I found:"
            ]))
            # Search TMDb for link
            tmdb_info = search_tmdb_movie(data.get('Title', movie_title), data.get('Year'))
            if tmdb_info:
                title_block = f'<a href="{tmdb_info["url"]}" target="_blank"><b>{data.get("Title", "Unknown")}</b></a> ({data.get("Year", "N/A")})'
            else:
                title_block = f'<b>{data.get("Title", "Unknown")}</b> ({data.get("Year", "N/A")})'
            response = f"{movie_intro}<br>{title_block}<br>"
            response += f"IMDB Rating: {data.get('imdbRating', 'N/A')}<br>"
            response += f"Plot: {data.get('Plot', 'No plot available.')}<br>"
            extra = get_personality_opinion_or_fact(data.get('Title', 'Unknown'))
            if extra:
                response += f"<br><i>{extra}</i>"
            return response
        else:
            return f"Sorry, I couldn't find info about {movie_title}."
        
    # Director intent
    match = re.search(r"(?:who directed|director(?: of| for| in)?|who is the director of)\s+(.+?)(?:[.?!]|$)", user_input_lower)
    if match:
        movie_title = match.group(1).strip(" .?!,")
        data = get_omdb_movie_info(movie_title)
        if data and data.get("Director"):
            response = f"The director of <b>{data.get('Title', 'Unknown')}</b> is {data['Director']}."
            return response
        else:
            return f"Sorry, I couldn't find the director for {movie_title}."

    # Stars intent
    match = re.search(r"(?:who starred in|star(?: of| in)?|stars in|who are the stars of)\s+(.+?)(?:[.?!]|$)", user_input_lower)
    if match:
        movie_title = match.group(1).strip(" .?!,")
        data = get_omdb_movie_info(movie_title)
        if data and data.get("Actors"):
            response = f"The stars of <b>{data.get('Title', 'Unknown')}</b> are {data['Actors']}."
            return response
        else:
            return f"Sorry, I couldn't find the stars for {movie_title}."

    # OMDb general info intent
    match = re.search(
        r"(?:get info (?:about|for|on)|tell me about|movie info|info (?:about|for|on)|what is|who is)\s+(.+?)(?:[.?!]|$)", user_input_lower
    )
    if match:
        movie_title = match.group(1).strip(" .?!,")
        data = get_omdb_movie_info(movie_title)
        if data:
            response = f"<b>{data.get('Title', 'Unknown')}</b> ({data.get('Year', 'N/A')})<br>"
            response += f"IMDB Rating: {data.get('imdbRating', 'N/A')}<br>"
            response += f"Plot: {data.get('Plot', 'No plot available.')}<br>"
            if data.get('Awards'):
                response += f"Fun Fact: {data['Awards']}<br>"
            return response
        else:
            return f"Sorry, I couldn't find info about {movie_title}."

    # Flexible restaurant queries (city, state, country, or zipcode)
    elif (
    "where can i eat" in user_input_lower
    or "places to eat" in user_input_lower
    or "good food" in user_input_lower
    or "restaurants near" in user_input_lower
    or "places to eat near" in user_input_lower
    or "restaurants in" in user_input_lower
    or "restaurant in" in user_input_lower  # Add this line
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
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            joke = get_random_joke(topic="restaurant")
            fact = get_wiki_fact(location)
            if not fact:
                fact = get_wiki_fact("restaurant")
            return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(restaurant_links) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"        
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
        joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
        fact = get_wiki_fact(city)
        if not fact:
            fact = get_wiki_fact("event")
        joke = get_random_joke(topic="event")
        return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(event_links) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
        

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
                joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
                joke = get_random_joke(topic="sightseeing")
                fact = get_wiki_fact(location)
                if not fact:
                    fact = get_wiki_fact("tourism")
                return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(sight_links) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
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
        joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
        joke = get_random_joke(topic="brewery")
        fact = get_wiki_fact(city)
        if not fact:
            fact = get_wiki_fact("brewery")
        return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(brewery_links) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
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
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            joke = get_random_joke(topic="recipe")
            fact = get_wiki_fact(ingredient)
            if not fact:
                fact = get_wiki_fact("recipe")
            return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(recipe_links) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
        else:
            return "Please specify an ingredient, e.g., 'recipes with chicken'."

    # Movies + Theaters (combined)
    elif "movies in" in user_input_lower or "movies near" in user_input_lower:
        if "movies in" in user_input_lower:
            city = user_input_lower.split("in")[-1].strip()
        else:
            city = user_input_lower.split("near")[-1].strip()
        movies = get_popular_movies()
        theaters = get_geoapify_places(city, category="entertainment.cinema")
        # Make movie titles clickable and add a fun fact/opinion for each
        movie_blocks = []
        for title, url in movies:
            tmdb_info = search_tmdb_movie(title)
            if tmdb_info:
                omdb_title = tmdb_info["title"]
                omdb_year = tmdb_info["year"]
                omdb_fact = get_personality_opinion_or_fact(omdb_title, omdb_year)
                block = f'<a href="{tmdb_info["url"]}" target="_blank"><strong>{omdb_title}</strong></a>'
                if omdb_fact:
                    block += f"<br><i>{omdb_fact}</i>"
                movie_blocks.append(block)
            else:
                # fallback to original
                omdb_fact = get_personality_opinion_or_fact(title)
                block = f'<a href="{url}" target="_blank"><strong>{title}</strong></a>'
                if omdb_fact:
                    block += f"<br><i>{omdb_fact}</i>"
                movie_blocks.append(block)
        intro = random.choice(PERSONALITY.get("movie_response_intros", ["Here are some popular movies right now:"]))
        movies_response = f"{intro}<br>" + "<br><br>".join(movie_blocks)
        # Make theater names clickable (Google Maps search)
        theater_links = [
            f'<a href="https://www.google.com/maps/search/{name.split(" - ")[0].replace(" ", "+")}+{city.replace(" ", "+")}" target="_blank">{name}</a>'
            for name in theaters
        ]
        theaters_response = f"<br><br>Here are some theaters in {city}:<br>" + "<br>".join(theater_links)
        joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
        joke = get_random_joke(topic="movie")
        fact = get_wiki_fact(city)
        if not fact:
            fact = get_wiki_fact("movie")
        return f"<strong>Activabot:</strong><br>" + movies_response + theaters_response + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
        

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
            # For each movie, get a fun fact/opinion
            movie_blocks = []
            for title, url in movies:
                fact = get_personality_opinion_or_fact(title)
                joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
                joke = get_random_joke(topic="movie")
                block = f'<a href="{url}" target="_blank"><strong>{title}</strong></a>'
                if fact:
                    block += f"<br><i>{fact}</i>"
                movie_blocks.append(block)
            # Use a personality-packed intro
            if genre and year:
                header = f"{random.choice(PERSONALITY.get('movie_response_intros', ['Movie time!']))} Here are some {genre.title()} movies from {year}:<br>"
            elif genre:
                header = f"{random.choice(PERSONALITY.get('movie_response_intros', ['Movie time!']))} Here are some {genre.title()} movies:<br>"
            elif year:
                header = f"{random.choice(PERSONALITY.get('movie_response_intros', ['Movie time!']))} Here are some movies from {year}:<br>"
            else:
                header = f"{random.choice(PERSONALITY.get('movie_response_intros', ['Movie time!']))} Here are some popular movies right now:<br>"
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            joke = get_random_joke(topic="movie")
            fact = get_wiki_fact(year if year else "movie")
            if not fact:
                fact = get_wiki_fact("movie")
            return header + "<br><br>".join(movie_blocks) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
            
            

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
    elif "book" in user_input_lower or "read" in user_input_lower or "novel" in user_input_lower:
    # Try to extract search type and value
        author_match = re.search(r"(?:author|by)\s+([a-zA-Z0-9 ,.'-]+)", user_input_lower)
        genre_match = re.search(r"(?:genre|type|kind of|category)\s+([a-zA-Z0-9 ,.'-]+)", user_input_lower)
        subject_match = re.search(r"(?:about|on|for|regarding|concerning|related to|subject)\s+([a-zA-Z0-9 ,.'-]+)", user_input_lower)
        
        # Default to subject if nothing else
        search_type = "subject"
        search_value = "fiction"
        if author_match:
            search_type = "author"
            search_value = author_match.group(1).strip()
        elif genre_match:
            search_type = "subject"
            search_value = genre_match.group(1).strip()
        elif subject_match:
            search_type = "subject"
            search_value = subject_match.group(1).strip()
        else:
            # fallback: try to extract a word after "book" or "novel"
            fallback_match = re.search(r"(?:book|novel|read)\s*(?:about|on|for)?\s*([a-zA-Z0-9 ,.'-]+)?", user_input_lower)
            if fallback_match and fallback_match.group(1):
                search_value = fallback_match.group(1).strip()

        # Google Books API
        google_books = []
        if search_type == "author":
            g_query = f"inauthor:{search_value}"
        else:
            g_query = f"subject:{search_value}"
        g_params = {"q": g_query, "maxResults": 5}
        g_response = requests.get("https://www.googleapis.com/books/v1/volumes", params=g_params)
        if g_response.status_code == 200:
            g_data = g_response.json()
            for book in g_data.get("items", []):
                info = book.get("volumeInfo", {})
                title = info.get("title", "Unknown Title")
                authors = ", ".join(info.get("authors", [])) if info.get("authors") else "Unknown Author"
                link = info.get("infoLink", "#")
                google_books.append(f'<a href="{link}" target="_blank"><strong>{title}</strong></a> by {authors} <span style="color:#888">(Google Books)</span>')

        # Open Library API
        openlibrary_books = []
        ol_params = {"limit": 5}
        if search_type == "author":
            ol_params["author"] = search_value
        else:
            ol_params["subject"] = search_value
        ol_response = requests.get("https://openlibrary.org/search.json", params=ol_params)
        if ol_response.status_code == 200:
            ol_data = ol_response.json()
            for doc in ol_data.get("docs", []):
                title = doc.get("title")
                author = ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Unknown author"
                year = doc.get("first_publish_year", "N/A")
                work_key = doc.get("key", "")
                link = f"https://openlibrary.org{work_key}" if work_key else "#"
                openlibrary_books.append(f'<a href="{link}" target="_blank"><strong>{title}</strong></a> by {author} ({year}) <span style="color:#888">(Open Library)</span>')

        all_books = google_books + openlibrary_books
        if all_books:
            intro = random.choice(PERSONALITY.get("book_intros", ["Here are some books you might like:"]))
            joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
            joke = get_random_joke(topic="book")
            fact = get_wiki_fact(search_value)
            if not fact:
                fact = get_wiki_fact("book")
            return f"<strong>Activabot:</strong><br>{intro}<br>" + "<br>".join(all_books) + f"<br><br><i>{joke_intro} {joke}</i><br><br>{fact}"
        else:
            return f"No books found for {search_value}."

    # Greetings
    elif "hello" in user_input_lower:
        return "Hello! How can I help you today?"

    # Fallback
    else:
        fallback = random.choice(PERSONALITY["fallbacks"]).replace("{bot_name}", bot_name)
        joke_intro = random.choice(PERSONALITY.get("joke_intros", ["Here's a joke:"]))
        joke = get_random_joke()
        return f"{fallback}<br><br><i>{joke_intro} {joke}</i>"

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