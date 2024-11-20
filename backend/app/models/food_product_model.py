from beanie import Document, Link
from pydantic import Field, HttpUrl
from typing import Optional
from app.models.food_brand_model import FoodBrand

class FoodProduct(Document):
    brand_id: Link[FoodBrand] = Field(..., description="Reference to the food brand")
    product_url: HttpUrl = Field(..., description="URL of the product page")
    title: str = Field(..., min_length=1, description="Title of the product")
    description: Optional[str] = Field(None, description="Description of the product")
    price: str = Field(..., min_length=1, description="Price of the product as a string")
    image_url: HttpUrl = Field(..., description="URL of the product image")
    food_category: str = Field(..., min_length=1, description="Category of the food item (e.g., Deal, Burger, etc.)")

    def __repr__(self) -> str:
        return f"<FoodProduct {self.title} ({self.food_category}) from {self.brand_id}>"

    def __str__(self) -> str:
        return self.title

    class Settings:
        name = "food_products"
