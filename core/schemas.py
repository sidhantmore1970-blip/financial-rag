from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterBody(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginBody(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleCreate(BaseModel):
    role_name: str
    permissions: str


class RoleOut(BaseModel):
    id: int
    role_name: str
    permissions: str

    model_config = {"from_attributes": True}


class AssignRoleBody(BaseModel):
    user_id: int
    role_id: int


class DocOut(BaseModel):
    id: int
    title: str
    company_name: str
    document_type: str
    uploaded_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocSearchParams(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    document_type: Optional[str] = None


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class ChunkOut(BaseModel):
    document_id: int
    title: str
    chunk_text: str
    score: float
