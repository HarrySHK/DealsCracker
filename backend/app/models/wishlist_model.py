from datetime import datetime
from beanie import Document, Link
from pydantic import Field
from typing import Union
from app.models.user_model import User
from app.models.clothing_product_model import ClothingProduct
from app.models.food_product_model import FoodProduct


class Wishlist(Document):
    userId: Link[User] = Field(..., description="Reference to the User model's ID")
    productId: Union[Link[ClothingProduct], Link[FoodProduct]] = Field(
        ..., description="Reference to the product's ID (clothing or food)"
    )
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="The creation date of the wishlist item")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="The last update date of the wishlist item")

    class Settings:
        name = "wishlists"

    def __repr__(self) -> str:
        return f"<Wishlist userId={self.userId}, productId={self.productId}>"

    def __str__(self) -> str:
        return f"Wishlist(userId={self.userId}, productId={self.productId})"