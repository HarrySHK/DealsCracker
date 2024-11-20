from beanie import Document
from pydantic import Field
from enum import Enum

class BrandName(str, Enum):
    ALKARAM = "Alkaram"
    J = "J."
    SAYA = "Saya"
    KHADDI = "Khaadi"
    ZEEN = "Zeen"
    DHANAK = "Dhanak"
    OUTFITTER = "Outfitter"

class ClothingBrand(Document):
    brand_name: BrandName = Field(..., description="The name of the clothing brand")

    def __repr__(self) -> str:
        return f"<ClothingBrand {self.brand_name}>"

    def __str__(self) -> str:
        return self.brand_name

    class Settings:
        name = "clothing_brands"
