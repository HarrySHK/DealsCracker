from app.schemas.user_schema import Signup, CreateProfile
from app.models.user_model import User, Location
from app.core.security import get_password,verify_password
from bson import ObjectId
from app.utils.fileUpload import upload_to_cloudinary
from fastapi import UploadFile, HTTPException, status
from app.core.security import create_access_token
from app.models.otp_model import Otp
from app.utils.emailSender import send_email
from app.utils.generateOtp import generate_otp
from datetime import datetime, timedelta

class UserService:
    @staticmethod
    async def create_user(user: Signup):
        # Check if the user already exists
        existing_user = await User.find_one({"email": user.email})
        if existing_user:
            raise ValueError("A user with this email already exists.")

        # Ensure valid role is provided (handled by the schema, but adding extra safety)
        if user.role not in ("User", "Admin"):
            raise ValueError("Invalid role. Role must be 'User' or 'Admin'.")

        # Create the User instance with the provided data
        user_instance = User(
            email=user.email,
            password=get_password(user.password),
            role=user.role,
        )

        # Save the user instance to MongoDB
        await user_instance.save()

        return {
            "_id": str(user_instance.id),
            "email": user_instance.email,
            "role": user_instance.role,
            "profilePicture": user_instance.profilePicture,
            "username": user_instance.username,
            "location": user_instance.location,
        }
    
    @staticmethod
    async def forget_password(email: str, role: str):
        # Check if the user exists
        user = await User.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email Address not found"
            )

        # Validate user type
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect user type"
            )

        # Generate OTP
        otp_code = generate_otp()

        # Calculate expiry time (1 minute from now)
        expiry_time = datetime.utcnow() + timedelta(minutes=1)

        # Save OTP in the database
        otp = Otp(
            userId=str(user.id),
            email=user.email,
            code=otp_code,
            expiry_time=expiry_time
        )
        await otp.save()

        # Send OTP to user's email
        subject = "Verification Code for Reset Password"
        content = f"Your verification code is: {otp_code}"
        await send_email(email, subject, content)

        # Generate a token for user
        token = create_access_token(str(user.id))

        return {
            "msg": "OTP sent to registered email",
            "access_token": token,
            "otp": otp_code
        }
    @staticmethod
    async def verify_otp(email: str, code: str):
        # Fetch the latest OTP for the provided email
        otp = await Otp.find({"email": email}).sort("-created_at").first_or_none()

        if not otp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTP not found"
            )

        # Validate OTP code
        if otp.code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )

        # Check if the OTP is already verified
        if otp.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP already verified"
            )

        # Check if OTP is expired
        if otp.expiry_time < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired"
            )

        # Mark OTP as verified
        otp.is_verified = True
        await otp.save()

        await otp.delete()
        return {"msg": "OTP verified successfully", "status": "success"}
    @staticmethod
    async def generate_otp(user_id: str):
        # Fetch the user by ID
        user = await User.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Generate a new OTP code
        otp_code = generate_otp()

        # Calculate the expiry time (e.g., 5 minutes from now)
        expiry_time = datetime.utcnow() + timedelta(minutes=1)

        # Check if an OTP document already exists for the user
        existing_otp = await Otp.find_one({"userId": str(user.id)})

        if existing_otp:
            # Update the existing OTP document
            existing_otp.code = otp_code
            existing_otp.expiry_time = expiry_time
            existing_otp.is_verified = False
            await existing_otp.save()
        else:
            # Create a new OTP document if none exists
            otp = Otp(
                userId=str(user.id),
                email=user.email,
                code=otp_code,
                expiry_time=expiry_time
            )
            await otp.save()

        # Send the OTP to the user's email
        subject = "Verification Code for Reset Password"
        content = f"Your verification code is: {otp_code}"
        await send_email(user.email, subject, content)

        token = create_access_token(str(user.id))

        return {
            "msg": "OTP resent to registered email",
            "access_token": token,
            "otp_code": otp_code  # Include the OTP code for debugging (remove in production)
        }
    @staticmethod
    async def reset_password(userId: str, password: str):
        # Validate input (assuming validation is handled in schema)
        
        # Find the user by email
        user = await User.find_one({"_id": userId})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        # Hash the new password
        hashed_password = get_password(password)

        # Update the user's password
        user.password = hashed_password
        await user.save()

        # Send a confirmation email (optional)
        subject = "Password Reset Successful"
        content = "Your password has been reset successfully. If this was not you, please contact support immediately."
        await send_email(user.email, subject, content)

        return {"msg": "Password reset successfully."}
    @staticmethod
    async def create_profile(user_id: str, profile_data: CreateProfile, profilePicture: UploadFile):
        # Validate user existence
        user = await User.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Create the Location object from the provided latitude and longitude
        location = Location(
            latitude=profile_data.location.latitude,
            longitude=profile_data.location.longitude
        ) if profile_data.location else None

        # Upload profile picture to Cloudinary
        uploaded_profile_picture_url = None
        if profilePicture:
            uploaded_profile_picture_url = await upload_to_cloudinary(profilePicture)
        
        # Update user's profile
        user.isProfileCompleted = True
        user.username = profile_data.username
        user.location = location
        if uploaded_profile_picture_url:
            user.profilePicture = uploaded_profile_picture_url

        # Save updates to the database
        await user.save()

        return {
            "message": "Profile updated successfully",
            "profile": {
                "_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "location": user.location.dict() if user.location else None,
                "profilePicture": user.profilePicture,
            },
        }
    @staticmethod
    async def authenticate(email: str, password: str) ->  User | None:
        user = await UserService.get_user_by_email(email=email)
        if not user:
            return None, "Email does not exist"
        if not verify_password(password=password, hash_pass=user.password):
            return None, "Incorrect password"
        
        return user, None 
    
    @staticmethod
    async def get_user_by_email(email: str) ->  User | None:
        user = await User.find_one(User.email == email)
        return user
    
    @staticmethod
    async def get_user_by_id(id: str) -> User | None:
        # user = await User.find_one(str(User.id) == id)
        print("ID: ",id)
        user = await User.find_one({"_id": ObjectId(id)})
        return user