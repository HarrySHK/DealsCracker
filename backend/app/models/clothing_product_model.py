from beanie import Document, Link
from pydantic import Field, HttpUrl
from typing import Optional
from app.models.clothing_brand_model import ClothingBrand
from datetime import datetime

class ClothingProduct(Document):
    brand_id: Link[ClothingBrand] = Field(..., description="Reference to the clothing brand")
    title: str = Field(..., min_length=1, description="Title of the product")
    product_page: HttpUrl = Field(..., description="URL of the product page")
    image_url: HttpUrl = Field(..., description="URL of the product image")
    original_price: float = Field(..., gt=0, description="Original price of the product")
    sale_price: Optional[float] = Field(None, ge=0, description="Sale price of the product, if available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the product was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the product was last updated")

    def __repr__(self) -> str:
        return f"<ClothingProduct {self.title} from {self.brand_id}>"

    def __str__(self) -> str:
        return self.title

    class Settings:
        name = "clothing_products"
