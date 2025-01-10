from datetime import datetime
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, BaseModel, EmailStr
from typing import Optional


class Role(str, Enum):
    ADMIN = "Admin"
    USER = "User"


class Location(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude of the user's location (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude of the user's location (-180 to 180)")


class User(Document):
    username: Optional[str] = None
    email: Indexed(EmailStr, unique=True)
    password: str
    location: Optional[Location] = None
    profilePicture: Optional[str] = None
    role: Role = Role.USER
    isProfileCompleted: bool = False

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False

    @property
    def create(self) -> datetime:
        return self.id.generation_time

    @classmethod
    async def by_email(cls, email: str) -> "User":
        return await cls.find_one(cls.email == email)

    class Settings:
        name = "users"
