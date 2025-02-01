from fastapi import FastAPI
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user_model import User
from app.models.clothing_brand_model import ClothingBrand
from app.models.clothing_product_model import ClothingProduct
from app.models.food_brand_model import FoodBrand
from app.models.food_product_model import FoodProduct
from app.models.otp_model import Otp
from app.models.wishlist_model import Wishlist
from app.models.contact_us_model import ContactUs
from app.api.api_v1.router import router
from app.services.clothing_service import schedule_clothing_scraping
from app.services.food_service import schedule_food_scraping
from app.services.wishlist_service import schedule_wishlist
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.getLogger("apscheduler").setLevel(logging.ERROR)

app = FastAPI(
    title = settings.PROJECT_NAME,
    openapi_url = f"{settings.API_VERSION}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.on_event("startup")
async def app_init():
    db_client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING).FarmStack

    await init_beanie(
        database = db_client,
        document_models = [
            User,
            ClothingBrand,
            ClothingProduct,
            FoodBrand,
            FoodProduct,
            Otp,
            Wishlist,
            ContactUs
        ]
    )
    print("Database connection initialized and models loaded.")
    schedule_clothing_scraping()
    schedule_food_scraping()
    schedule_wishlist()
    
app.include_router(router,prefix=settings.API_VERSION)