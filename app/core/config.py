# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, AnyHttpUrl
from typing import Optional, List, Union
import json


class Settings(BaseSettings):
    # Project Meta
    PROJECT_NAME: str = "Optivus Protocol API"
    API_V1_STR: str = "/api"
    
    # Supabase Database (Async URL)
    DATABASE_URL: PostgresDsn
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_KEY: str

    # JWT
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLIC_KEY: str
    STRIPE_WEBHOOK_SECRET: str

   

    class Config:
        case_sensitive = True
        env_file = ".env"

        extra = "ignore"


settings = Settings()