from beanie import Document
from pydantic import Field
from enum import Enum
from datetime import datetime

class BrandName(str, Enum):
    ALKARAM = "Alkaram"
    J = "J."
    SAYA = "Saya"
    KHADDI = "Khaadi"
    ZEEN = "Zeen"
    DHANAK = "Dhanak"
    OUTFITTER = "Outfitters"

class ClothingBrand(Document):
    brand_name: BrandName = Field(..., description="The name of the clothing brand")
    banner_image: str = Field(..., description="The URL of the brand's banner image")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="The creation date of the document")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="The last update date of the document")

    def __repr__(self) -> str:
        return f"<ClothingBrand {self.brand_name}>"

    def __str__(self) -> str:
        return self.brand_name

    class Settings:
        name = "clothing_brands"
