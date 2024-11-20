from beanie import Document
from pydantic import Field
from enum import Enum

class BrandName(str, Enum):
    KFC = "Kababjees Fried Chicken"
    ANGEETHI = "Angeethi"
    DELIZIA = "Delizia"
    FOODS_INN = "Foods Inn"
    GINSOY = "Ginsoy"
    HOT_N_SPICY = "Hot n Spicy"
    KARACHI_BROAST = "Karachi Broast"
    KAYBEES = "Kaybees"
    PIZZA_POINT = "Pizza Point"
    TOOSO = "Tooso"

class FoodBrand(Document):
    brand_name: BrandName = Field(..., description="The name of the food brand")

    def __repr__(self) -> str:
        return f"<FoodBrand {self.brand_name}>"

    def __str__(self) -> str:
        return self.brand_name

    class Settings:
        name = "food_brands"
