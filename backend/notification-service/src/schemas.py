
from pydantic import BaseModel, EmailStr


class UserCreatedMessage(BaseModel):
    username: str
    email: EmailStr


class UserDeletedMessage(BaseModel):
    email: EmailStr


class ProductCreatedMessage(BaseModel):
    product_name: str
    created_by: str


class ProductDeletedMessage(BaseModel):
    product_name: str
    deleted_by: str


class ReviewMessage(BaseModel):
    product_id: str
    user_email: EmailStr
