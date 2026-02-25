from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from uuid import UUID, uuid4

class ProjectBase(SQLModel):
    name: str
    description: Optional[str] = None
    scene_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

class Project(ProjectBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scene_data: Optional[Dict[str, Any]] = None
