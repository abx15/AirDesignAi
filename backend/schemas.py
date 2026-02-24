from datetime import datetime
from typing import Any, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EquationCreate(BaseModel):
    expression: str
    solution: Optional[str] = None
    steps: Optional[str] = None
    graph_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


class EquationRead(BaseModel):
    id: UUID
    user_id: UUID
    expression: str
    solution: Optional[str]
    steps: Optional[str]
    graph_data: Optional[Dict[str, Any]]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SolveRequest(BaseModel):
    image_base64: str


class SolveResponse(BaseModel):
    expression: str
    solution: str
    steps: str
    graph_data: Optional[Dict[str, Any]]
    confidence: float


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

