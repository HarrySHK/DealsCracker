from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.services.clothingAndFoodApi_service import ClothingAndFoodService
from app.api.deps.user_deps import get_current_user
from app.models.user_model import User

clothing_and_food_router = APIRouter()

@clothing_and_food_router.get("/getAllBrandsBanner", summary="Get random banners from brands")
async def get_all_brands_banner(
    category: str = Query(..., description="Category of banners to fetch (clothing, food, both)")
):
    try:
        # Validate category
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, both"
            )

        # Fetch banners
        result = await ClothingAndFoodService.get_random_brands_banner(category)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@clothing_and_food_router.get("/getTodaysBestDeals", summary="Get today's best deals")
async def get_todays_best_deals(
    category: str = Query(..., description="Category of deals to fetch (clothing, food, both)")
):
    try:
        # Validate category
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, both"
            )

        # Fetch deals
        result = await ClothingAndFoodService.get_todays_best_deals(category)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@clothing_and_food_router.get("/getTop5Products", summary="Get Top 5 Products")
async def get_todays_best_deals(
    category: str = Query(..., description="Category of deals to fetch (clothing, food, both)")
):
    try:
        # Validate category
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, both"
            )

        # Fetch deals
        result = await ClothingAndFoodService.get_top_5_products(category)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@clothing_and_food_router.get("/getTopTrendingBrands", summary="Get Top Tending Brands")
async def get_top_trending_brands(
    category: str = Query(..., description="Category of deals to fetch (clothing, food, both)")
):
    try:
        # Validate category
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, both"
            )

        # Fetch deals
        result = await ClothingAndFoodService.get_top_trending_brands(category)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@clothing_and_food_router.get("/getAllBrands", summary="Get All Brands")
async def get_top_trending_brands(
    category: str = Query(..., description="Category of Brands to fetch (clothing, food, both)")
):
    try:
        # Validate category
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, both"
            )

        # Fetch deals
        result = await ClothingAndFoodService.get_all_brands(category)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@clothing_and_food_router.get("/getAllProducts", summary="Get All Products")
async def get_all_products(
    category: str = Query(
        None,
        description="Category of products to fetch (clothing, food, or both)"
    ),
    page: int = Query(
        1,
        description="Page number for pagination (default is 1)"
    ),
    limit: int = Query(
        10,
        description="Number of items per page for pagination (default is 10)"
    ),
    search: str = Query(
        None,
        description="Search query to filter products by title or brand name"
    ),
    brand_name: str = Query(
        None,
        description="Filter products by brand name (case-insensitive)"
    ),
    latest: bool = Query(
        True,
        description="Sort products by created date (True for latest first, False for oldest first)"
    ),
    sortPrice: str = Query(
        None,
        description="Sort products by price (ascending or descending)"
    ),
):
    try:
        # Validate category input
        if category not in [None, "clothing", "food", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category. Must be one of: clothing, food, or both."
            )
        if sortPrice and sortPrice not in ["ascending", "descending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sortPrice. Must be one of: ascending, descending."
            )

        # Fetch products from the service
        result = await ClothingAndFoodService.get_all_products(
            category=category,
            page=page,
            limit=limit,
            search=search,
            brand_name=brand_name,
            latest=latest,
            sortPrice=sortPrice
        )
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    
@clothing_and_food_router.get("/getNearbyOutlets", summary="Get nearby outlets")
async def get_nearby_outlets(category: str, current_user: User = Depends(get_current_user)):
    try:
        if category not in ["clothing", "food", "both"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid category. Choose from 'clothing', 'food', or 'both'."
            )

        outlets = await ClothingAndFoodService.get_nearby_outlets(category=category, user=current_user)
        return {"nearby_outlets": outlets}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
