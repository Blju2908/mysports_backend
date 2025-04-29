from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from sqlmodel import SQLModel, Session, select
from app.core.supabase import get_supabase_client
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], table_name: str):
        """
        CRUD object with default methods to create, read, update, delete (CRUD).
        
        **Parameters**
        * `model`: A SQLModel model class
        * `table_name`: Supabase table name
        """
        self.model = model
        self.table_name = table_name
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Get a record by id
        """
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).select("*").eq("id", id).execute()
        if response.data and len(response.data) > 0:
            return self.model(**response.data[0])
        return None
    
    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple records
        """
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).select("*").range(skip, skip + limit - 1).execute()
        return [self.model(**item) for item in response.data]
    
    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        """
        obj_in_data = obj_in.model_dump()
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).insert(obj_in_data).execute()
        return self.model(**response.data[0])
    
    async def update(self, *, id: Any, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """
        Update a record
        """
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).update(obj_in_data).eq("id", id).execute()
        if response.data and len(response.data) > 0:
            return self.model(**response.data[0])
        return None
    
    async def remove(self, *, id: Any) -> bool:
        """
        Delete a record
        """
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).delete().eq("id", id).execute()
        return len(response.data) > 0
    
    async def get_by_field(self, field: str, value: Any) -> List[ModelType]:
        """
        Get records by field value
        """
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).select("*").eq(field, value).execute()
        return [self.model(**item) for item in response.data]
            
    async def create_many(self, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records
        """
        objs_data = [obj.model_dump() for obj in objs_in]
        supabase = get_supabase_client()
        response = supabase.table(self.table_name).insert(objs_data).execute()
        return [self.model(**item) for item in response.data] 