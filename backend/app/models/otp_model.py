from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime


class Otp(Document):
    userId: str = Field(..., description="User ID from User model")
    email: EmailStr = Field(..., description="Email address associated with the OTP")
    code: str = Field(..., description="OTP code")
    is_verified: bool = Field(default=False, description="Verification status of the OTP")
    expiry_time: datetime = Field(..., description="OTP expiry time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="OTP creation time")

    class Settings:
        name = "otps"
