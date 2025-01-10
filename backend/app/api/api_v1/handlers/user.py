import pymongo.errors
from fastapi import APIRouter, HTTPException,status, UploadFile, Depends, Form
from app.schemas.user_schema import Signup, CreateProfile, ResetPasswordSchema
from app.services.user_service import UserService
from app.models.user_model import User
from app.api.deps.user_deps import get_current_user
from pydantic import ValidationError
import pymongo
from pydantic import BaseModel, EmailStr
from bson import ObjectId

user_router = APIRouter()

@user_router.post("/signup", summary="Create new user")
async def create_user(data: Signup):
    try:
        return await UserService.create_user(data)
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
    
@user_router.post("/create_profile", summary="Create or update user profile")
async def create_profile(
    username: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    profilePicture: UploadFile = None,
    current_user: User = Depends(get_current_user)
):
    try:
        # Prepare the CreateProfile data
        data = CreateProfile(username=username, location={"latitude": latitude, "longitude": longitude})

        # Call the service to update the profile
        result = await UserService.create_profile(
            user_id=str(current_user.id),
            profile_data=data,
            profilePicture=profilePicture,
        )
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=ve.errors())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
class ForgetPasswordRequest(BaseModel):
    email: EmailStr
    role: str


@user_router.post("/forget-password", summary="Send OTP for password reset")
async def forget_password(request: ForgetPasswordRequest):
    try:
        return await UserService.forget_password(request.email, request.role)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
    
class VerifyOtpRequest(BaseModel):
    code: str

# @user_router.post("/verify-otp", summary="Verify OTP for password reset")
# async def verify_otp(request: VerifyOtpRequest, current_user: User = Depends(get_current_user)):
#     try:
#         # Get the email from the user model using the current user's id
#         print(f"User ID: {type(current_user.id)}")
#         user = await User.find_one({"_id": ObjectId(current_user.id)})
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
#         email = user.email 

#         # Call the service to verify OTP
#         result = await UserService.verify_otp(email=email, code=request.code)

#         return result

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An unexpected error occurred. Please try again later."
#         )

@user_router.post("/verify-otp", summary="Verify OTP for password reset")
async def verify_otp(request: VerifyOtpRequest, current_user: User = Depends(get_current_user)):
    try:
        print(f"User ID Type: {type(current_user.id)}")  # Debug log
        
        user = await User.find_one({"_id": ObjectId(current_user.id)})
        if not user:
            print("User not found in the database")  # Debug log
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        email = user.email
        print(f"User email: {email}")  # Debug log

        # Call the service to verify OTP
        print(f"Verifying OTP for email: {email} with code: {request.code}")  # Debug log
        result = await UserService.verify_otp(email=email, code=request.code)
        print(f"OTP Verification Result: {result}")  # Debug log

        return result

    except HTTPException as e:
        print(f"HTTP Exception: {e.detail}")  # Debug log
        raise e
    except Exception as e:
        print(f"Unexpected error: {e}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )

@user_router.post("/generate-otp", summary="Resend OTP for a user")
async def generate_otp(current_user: User = Depends(get_current_user)):
    try:
        result = await UserService.generate_otp(user_id=str(current_user.id))
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {e}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
    
@user_router.put("/reset-password", summary="Reset user password")
async def reset_password(
    reset_password_data: ResetPasswordSchema,
    current_user: User = Depends(get_current_user),
):
    try:
        # Extract user ID from current_user
        userId = ObjectId(current_user.id)

        # Call service method to reset password
        result = await UserService.reset_password(userId=userId, password=reset_password_data.password)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )