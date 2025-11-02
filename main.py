from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import random

load_dotenv()  # Load .env variables

api_key = os.getenv("IMBD_API_KEY")
app = FastAPI()

# Allow requests from your frontend (or all origins for testing)
origins = [
    "*",  # allow all origins (for testing only)
    # "http://localhost:3000",  # you can restrict to your frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods: GET, POST, OPTIONS…
    allow_headers=["*"],  # allow all headers
)

# Load data
movies = joblib.load("model/movies_data.joblib")
similarity = joblib.load("model/recommend_system.joblib")


class MovieRequest(BaseModel):
    movie_name: str


# Welcome route
@app.get("/")
def welcome_page():
    return {"message": "Hello, welcome to my movie recommendation API"}


DEFAULT_POSTER = "https://via.placeholder.com/500x750?text=No+Poster"


# Helper function to fetch posters
def fetch_poster(movie_id):
    if not movie_id:
        return None  # no movie ID available
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # raise HTTPError for bad responses
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            return None
    except requests.RequestException:
        # fallback: return None or a default poster URL
        return None


# Recommendation endpoint
@app.post("/recommend")
def recommend_movie(request: MovieRequest):  # -> dict[str, str] | dict[str, list[Any]]:
    movie = request.movie_name.strip()
    movie: str = str(movie)
    # Case-insensitive match
    matched = movies[movies["title"].str.lower() == movie.lower()]
    if matched.empty:
        # Optional: fallback to fuzzy matching
        from difflib import get_close_matches

        closest = get_close_matches(movie, movies["title"].tolist(), n=1, cutoff=0.6)
        if not closest:
            return {"error": f"Movie '{movie}' not found"}
        matched = movies[movies["title"] == closest[0]]

    idx = matched.index[0]
    distances = similarity[idx]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[
        1:9
    ]

    recommendations = []
    for i in movie_list:
        movie_title = movies.iloc[i[0]]["title"]
        # Use the correct column name for movie ID
        movie_id = movies.iloc[i[0]]["id"]  # <-- make sure this column exists
        recommendations.append(
            {"title": movies.iloc[i[0]]["title"], "poster": fetch_poster(movie_id)}
        )

    return {"recommendations": recommendations}


class SearchRequest(BaseModel):
    query: str


@app.get("/search")
def search_movies(query: str = ""):
    if not query:
        return {"suggestions": []}

    results = movies[movies["title"].str.contains(query, case=False, na=False)]
    suggestions = results["title"].head(10).tolist()
    return {"suggestions": suggestions}


@app.get("/movie_of_the_day")
def movie_of_the_day():

    random.seed(12)
    return random.choice(movies["title"].tolist())


@app.post("/genre/{genre}")
def get_genre(genre: str = ""):
    random.seed(4)
    return random.choice(movies[movies["genre_names"].str.contains("action", case=False, na=False)]["title"].tolist())
    


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
