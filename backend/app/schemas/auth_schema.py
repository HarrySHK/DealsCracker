from pydantic import BaseModel, EmailStr, Field, ValidationError, root_validator

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str

class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None

class LoginRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="User email is required")
    password: str = Field(..., min_length=8, max_length=24, description="User password must be between 8-24 characters")

    @root_validator(pre=True)
    def check_not_empty(cls, values):
        email = values.get('email')
        password = values.get('password')

        if not email:
            raise ValueError('Email cannot be empty')

        if not password or password.strip() == "":
            raise ValueError('Password cannot be empty')

        return values