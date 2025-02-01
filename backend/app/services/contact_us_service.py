from app.models.contact_us_model import ContactUs
from fastapi import HTTPException, status
from app.schemas.contact_us_schema import ContactUsSchema

class ContactUsService:
    @staticmethod
    async def send_message(data: ContactUsSchema):
        try:
            # Create ContactUs instance
            contact_us_instance = ContactUs(
                firstName=data.firstName,
                lastName=data.lastName,
                email=data.email,
                phoneNumber=data.phoneNumber,
                message=data.message
            )

            # Save to database
            await contact_us_instance.save()

            return {"message": "Your message has been sent successfully!"}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while sending the message."
            )
