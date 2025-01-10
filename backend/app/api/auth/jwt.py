from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth_schema import TokenSchema
from app.models.user_model import User
from app.api.deps.user_deps import get_current_user
from app.core.config import settings
from app.schemas.auth_schema import TokenPayload, LoginRequestSchema
from pydantic import ValidationError
from jose import jwt


auth_router = APIRouter()


@auth_router.post('/login', summary="Create access and refresh tokens for user")
async def login(form_data: LoginRequestSchema):
    user, error = await UserService.authenticate(email=form_data.email, password=form_data.password)
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # return {
    #     "access_token": create_access_token(str(user.id)),
    #     "refresh_token": create_refresh_token(str(user.id)),
    #     "userDetails": {
    #         "_id": str(user.id),
    #         "username": user.username,
    #         "email": user.email,
    #         "role": user.role,
    #         "location": user.location,
    #         "profilePicture": user.profilePicture
    #     }
    # }
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Prepare the response
    response = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "userDetails": {
            "_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "location": user.location,
            "profilePicture": user.profilePicture,
        }
    }

    # Check if the profile is completed
    if not user.isProfileCompleted:
        response["detail"] = "Please complete your profile before logging in."

    return response

@auth_router.post('/test-token', summary="Test if the access token is valid")
async def test_token(user: User = Depends(get_current_user)):
    return {
            "_id": str(user.id),
            "username": user.username,
            "email": user.email
        }


@auth_router.post('/refresh', summary="Refresh token", response_model=TokenSchema)
async def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await UserService.get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token for user",
        )
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
    }