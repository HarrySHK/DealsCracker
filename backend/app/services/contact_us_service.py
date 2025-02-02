from app.models.contact_us_model import ContactUs
from fastapi import HTTPException, status
from app.schemas.contact_us_schema import ContactUsSchema
from math import ceil
from pymongo import DESCENDING

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
    @staticmethod
    async def get_all_contact_queries(search: str = None, page: int = 1, limit: int = 10):
        try:
            print("✅ Debug: Entered get_all_contact_queries")  # Debug log

            # Ensure valid pagination values
            page = max(1, page)
            limit = max(1, limit)

            # Calculate skip value for pagination
            skip = (page - 1) * limit

            # Build search query (Beanie Query Format)
            search_filter = {}
            if search:
                search_regex = {"$regex": search, "$options": "i"}  # Case-insensitive regex
                search_filter = {
                    "$or": [
                        {"firstName": search_regex},
                        {"lastName": search_regex},
                        {"email": search_regex},
                        {"message": search_regex},
                    ]
                }

            print(f"🔍 Search Filter: {search_filter}")  # Debug log

            # Get total count
            total_count = await ContactUs.find(search_filter).count()
            print(f"🔢 Total Count: {total_count}")  # Debug log

            if total_count == 0:
                return {
                    "message": "No contact queries found.",
                    "queries": [],
                    "totalQueries": 0,
                    "totalPages": 0,
                    "currentPage": page,
                }

            # Fetch paginated data, sorted by `createdAt` descending (-1)
            contact_queries = await ContactUs.find(search_filter).sort(-ContactUs.createdAt).skip(skip).limit(limit).to_list()

            print(f"📄 Retrieved Queries: {contact_queries}")  # Debug log

            # Convert ObjectId to string
            formatted_data = [
                {
                    "_id": str(query.id),
                    "firstName": query.firstName,
                    "lastName": query.lastName,
                    "email": query.email,
                    "phoneNumber": query.phoneNumber,
                    "message": query.message,
                    "createdAt": query.createdAt.isoformat(),
                }
                for query in contact_queries
            ]

            return {
                "currentPage": page,
                "totalPages": ceil(total_count / limit),
                "totalQueries": total_count,
                "queries": formatted_data,
            }

        except Exception as e:
            print(f"❌ Error: {str(e)}")  # Debug log
            raise HTTPException(status_code=500, detail=f"Error retrieving contact queries: {str(e)}")
