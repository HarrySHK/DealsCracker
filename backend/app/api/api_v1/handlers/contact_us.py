from fastapi import APIRouter, HTTPException, status, Query
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

@contact_us_router.get("/getAllContactQueries", summary="Get All Contact Queries")
async def get_all_contact_queries(
    search: str = Query(
        None,
        description="Search query to filter contact messages by first name, last name, email, or message"
    ),
    page: int = Query(
        1,
        description="Page number for pagination (default is 1)"
    ),
    limit: int = Query(
        10,
        description="Number of items per page for pagination (default is 10)"
    ),
):
    try:
        # Fetch contact queries from the service
        result = await ContactUsService.get_all_contact_queries(
            search=search,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contact queries: {str(e)}"
        )