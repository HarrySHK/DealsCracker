from beanie import Document, Link
from pydantic import Field, HttpUrl
from typing import Optional
from app.models.food_brand_model import FoodBrand
from datetime import datetime


class FoodProduct(Document):
    brand_id: Link[FoodBrand] = Field(..., description="Reference to the food brand")
    product_url: HttpUrl = Field(..., description="URL of the product page")
    title: str = Field(..., min_length=1, description="Title of the product")
    description: Optional[str] = Field(None, description="Description of the product")
    # original_price: Optional[str] = Field(None, description="Original price of the product")
    # discount_price: Optional[str] = Field(None, description="Discounted price of the product")
    original_price: Optional[float] = Field(None, gt=0, description="Original price of the product")  # Changed to float
    discount_price: Optional[float] = Field(None, ge=0, description="Discounted price of the product")
    image_url: HttpUrl = Field(..., description="URL of the product image")
    food_category: str = Field(..., min_length=1, description="Category of the food item (e.g., Deal, Burger, etc.)")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the product was created")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the product was last updated")

    def __repr__(self) -> str:
        return f"<FoodProduct {self.title} ({self.food_category}) from {self.brand_id}>"

    def __str__(self) -> str:
        return self.title

    class Settings:
        name = "food_products"
