from pydantic import BaseModel, EmailStr

class ContactUsSchema(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phoneNumber: str
    message: str
