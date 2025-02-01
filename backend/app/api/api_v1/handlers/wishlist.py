from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from app.services.wishlist_service import WishlistService
from app.api.deps.user_deps import get_current_user
from app.models.user_model import User

# Create the router for wishlist
wishlist_router = APIRouter()


@wishlist_router.put("/toggleWishlist", summary="Add or remove a product from the wishlist")
async def toggle_wishlist_item(
    productId: str = Query(..., description="ID of the product to toggle in the wishlist"),
    current_user: User = Depends(get_current_user),
):
    try:
        # Ensure the productId is a valid ObjectId
        product_id = ObjectId(productId)

        # Call the service to toggle the wishlist item
        result = await WishlistService.toggle_wishlist(user_id=str(current_user.id), product_id=product_id)
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@wishlist_router.get("/getUserWishlist", summary="Get user's wishlist")
async def get_user_wishlist(current_user: User = Depends(get_current_user)):
    try:
        # Fetch the user's wishlist using the service
        wishlist = await WishlistService.get_user_wishlist(user_id=str(current_user.id))
        return {"wishlist": wishlist}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )