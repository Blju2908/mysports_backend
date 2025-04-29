from pydantic import BaseModel, EmailStr

class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str 