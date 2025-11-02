from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import random

load_dotenv()  # Load .env variables
movies = joblib.load("model/movies_data.joblib")
api_key = os.getenv("IMBD_API_KEY")
app = FastAPI()

# @app.post("/genre/{genre}")
def get_genre(genre: str = ""):
    random.seed(4)
    return random.choice(movies[movies["genres"] == genre]["title"].tolist())

# genres = [{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 14, "name": "Fantasy"}, {"id": 878, "name": "Science Fiction"}]
print(get_genre("Action"))
