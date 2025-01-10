from fastapi import APIRouter, HTTPException, status, Query
from app.services.clothingApi_service import ClothingService

clothing_router = APIRouter()

@clothing_router.get("/getAllClothingProducts", summary="Get all clothing products with pagination")
async def get_all_clothing_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, description="Number of items per page"),
    search: str = Query(None, description="Search query (e.g., title or brand name)"),
    brand_name: str = Query(None, description="Filter by brand name")
):
    try:
        products = await ClothingService.get_all_clothing_products(page, limit, search, brand_name)
        return products
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )