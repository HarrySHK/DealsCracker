from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field, BaseModel, EmailStr
from typing import Optional

class ContactUs(Document):
    firstName: str = Field(..., description="User's First Name")
    lastName: str = Field(..., description="User's Last Name")
    email: Indexed(EmailStr, unique=False)
    phoneNumber: str = Field(..., description="User's Phone Number")
    message: str = Field(..., description="User's message")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="The date when the message was sent")

    class Settings:
        name = "contact_us"

    def __repr__(self) -> str:
        return f"<ContactUs {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ContactUs):
            return self.email == other.email
        return False
