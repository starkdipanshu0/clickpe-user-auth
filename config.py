import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

class Config:
    # ---- Base App Config ----
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # ---- SQLAlchemy / Database ----
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- JWT ----
    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-dev-secret")
    JWT_ALGORITHM = "HS256"

    # ---- Google OAuth ----
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI", 
        "http://localhost:5000/auth/google/callback"
    )

    # ---- GitHub OAuth ----
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = os.getenv(
        "GITHUB_REDIRECT_URI",
        "http://localhost:5000/auth/github/callback"
    )
