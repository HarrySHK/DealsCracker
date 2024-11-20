from beanie import Document, Link
from pydantic import Field, HttpUrl
from typing import Optional
from app.models.clothing_brand_model import ClothingBrand

class ClothingProduct(Document):
    brand_id: Link[ClothingBrand] = Field(..., description="Reference to the clothing brand")
    title: str = Field(..., min_length=1, description="Title of the product")
    product_page: HttpUrl = Field(..., description="URL of the product page")
    image_url: HttpUrl = Field(..., description="URL of the product image")
    # original_price: float = Field(..., gt=0, description="Original price of the product")
    # sale_price: Optional[float] = Field(None, ge=0, description="Sale price of the product, if available")
    original_price: str = Field(..., min_length=1, description="Original price of the product as a string")
    sale_price: Optional[str] = Field(None, min_length=1, description="Sale price of the product as a string, if available")

    def __repr__(self) -> str:
        return f"<ClothingProduct {self.title} from {self.brand_id}>"

    def __str__(self) -> str:
        return self.title

    class Settings:
        name = "clothing_products"
