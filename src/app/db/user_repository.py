from app.db.crud import CRUDBase
from app.models.user_model import UserModel
from typing import List, Optional, Any
from app.core.supabase import get_supabase_client
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    profile_image: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = None

class UserRepository(CRUDBase[UserModel, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(UserModel, "users")
    
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email
        """
        results = await self.get_by_field("email", email)
        return results[0] if results else None
    
    async def update_last_login(self, id: UUID) -> Optional[UserModel]:
        """
        Update the user's last login timestamp
        """
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).update({
            "last_login_at": datetime.utcnow().isoformat()
        }).eq("id", str(id)).execute()
        
        if response.data and len(response.data) > 0:
            return UserModel(**response.data[0])
        return None

    async def deactivate_user(self, id: UUID) -> bool:
        """
        Deactivate a user (set is_active to False)
        """
        update_data = UserUpdate(is_active=False)
        user = await self.update(id=id, obj_in=update_data)
        return user is not None

# Create a singleton instance
user_repository = UserRepository() 