from fastapi import APIRouter
from app.api.api_v1.handlers import user,clothing, clothingAndFood, wishlist,contact_us
from app.api.auth.jwt import auth_router

router = APIRouter()

router.include_router(user.user_router,prefix="/user",tags=["user"])
router.include_router(auth_router,prefix="/auth",tags=["auth"])
router.include_router(clothing.clothing_router,prefix="/clothing",tags=["clothing"])
router.include_router(clothingAndFood.clothing_and_food_router,prefix="/clothingAndFood",tags=["clothingAndFood"])
router.include_router(wishlist.wishlist_router,prefix="/wishlist",tags=["wishlist"])
router.include_router(contact_us.contact_us_router,prefix="/contactUs",tags=["contactUs"])