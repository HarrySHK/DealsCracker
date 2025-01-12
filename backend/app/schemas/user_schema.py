from pydantic import BaseModel, EmailStr, Field, field_validator, FieldValidationInfo
from enum import Enum
from app.models.user_model import Location, Role
from typing import Optional


class Signup(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, max_length=24, description="User password")
    role: Role = Field(default=Role.USER, description="User role, either 'Admin' or 'User'")

    # Custom validation for email
    @field_validator('email', mode='before')
    def validate_email(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(f'{info.field_name.capitalize()} is required')
        return v

    # Custom validation for password
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 24:
            raise ValueError('Password cannot exceed 24 characters')
        return v

    # Custom validation for role
    @field_validator('role', mode='before')
    def validate_role(cls, v):
        if v not in ("User", "Admin"):
            raise ValueError("Role must be 'User' or 'Admin'")
        return v
    
class CreateProfile(BaseModel):
    username: str = Field(..., min_length=5, max_length=50, description="User's username")
    location: Location = Field(..., description="User's location containing latitude and longitude")

    # Custom validation for username length
    @field_validator('username')
    def validate_username(cls, v):
        if len(v) < 5:
            raise ValueError('Username must be at least 5 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        return v

    # Custom validation for location
    @field_validator('location', mode='before')
    def validate_location(cls, v):
        if not v:
            raise ValueError('Location is required')
        return v

class UpdateProfile(BaseModel):
    username: Optional[str] = None
    location: Optional[Location] = None

class ResetPasswordSchema(BaseModel):
    password: str = Field(..., min_length=8, description="New password with at least 8 characters.")