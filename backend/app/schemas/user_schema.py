from pydantic import BaseModel,EmailStr, Field, field_validator, FieldValidationInfo

class UserAuth(BaseModel):
    email: EmailStr = Field(...,description="user email")
    username: str = Field(..., min_length=5, max_length=50, description="user username")
    password: str = Field(..., min_length=8, max_length=24, description="user password")

     # Custom validation for empty fields
    @field_validator('email', 'username', 'password',  mode='before')
    def not_empty(cls, v, info: FieldValidationInfo):
        if v is None or v == '':
            raise ValueError(f'{info.field_name.capitalize()} is required')
        return v

    # Custom validation for username length
    @field_validator('username')
    def username_length(cls, v):
        if len(v) < 5:
            raise ValueError('Username must be at least 5 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        return v

    # Custom validation for password length
    @field_validator('password')
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 24:
            raise ValueError('Password cannot exceed 24 characters')
        return v
