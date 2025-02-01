from fastapi import APIRouter, HTTPException, status
from app.schemas.contact_us_schema import ContactUsSchema
from app.services.contact_us_service import ContactUsService

contact_us_router = APIRouter()

@contact_us_router.post("/contact-us", summary="Send a contact message")
async def send_contact_message(data: ContactUsSchema):
    try:
        return await ContactUsService.send_message(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
