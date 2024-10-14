from app.schemas.user_schema import UserAuth
from app.models.user_model import User
from app.core.security import get_password,verify_password
from bson import ObjectId

class UserService:
    @staticmethod
    async def create_user(user:UserAuth):
        user_instance = User(
            username=user.username,
            email=user.email,
            password=get_password(user.password)
        )
        await user_instance.save()
        print(user_instance.dict())
        return {
            "_id": str(user_instance.id),
            "username": user_instance.username,
            "email": user_instance.email,
            "first_name": user_instance.first_name,
            "last_name": user_instance.last_name,
            "disabled": user_instance.disabled
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