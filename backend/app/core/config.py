from decouple import config
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    API_VERSION: str = config("API_VERSION", cast=str)
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", cast=str)
    JWT_REFRESH_SECRET_KEY: str = config("JWT_REFRESH_SECRET_KEY", cast=str)
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = config("REFRESH_TOKEN_EXPIRE_MINUTES", cast=int)
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
        "http://localhost:3000"
    ]
    # Email sender
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = "haris.g20499@iqra.edu.pk"
    SMTP_PASSWORD: str = "xddjxuuhpuptnaqn"
    EMAIL_SENDER: str = "haris.g20499@iqra.edu.pk"
    EMAIL_FROM_NAME: str = "DealsCracker"    
    PROJECT_NAME: str = "FARMSTACK_CRUD"    
    # Database
    MONGO_CONNECTION_STRING: str = config("MONGO_CONNECTION_STRING", cast=str)    
    # Google Map API
    GOOGLE_MAPS_API_KEY: str = config("GOOGLE_MAPS_API_KEY", cast=str)    
    # Cloudinary Creds
    CLOUDINARY_CLOUD_NAME: str = config("CLOUDINARY_CLOUD_NAME", cast=str)    
    CLOUDINARY_API_KEY: str = config("CLOUDINARY_API_KEY", cast=str)    
    CLOUDINARY_API_SECRET: str = config("CLOUDINARY_API_SECRET", cast=str)    
    class Config:
        case_sensitive = True
        
settings = Settings()