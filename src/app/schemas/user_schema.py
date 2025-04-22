from pydantic import BaseModel, EmailStr

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str 