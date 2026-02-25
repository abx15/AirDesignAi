from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate, 
    session: AsyncSession = Depends(get_session)
):
    return await ProjectService.create_project(session, project_in)

@router.get("/", response_model=List[Project])
async def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    session: AsyncSession = Depends(get_session)
):
    return await ProjectService.get_projects(session, skip, limit)

@router.get("/{project_id}", response_model=Project)
async def read_project(
    project_id: UUID, 
    session: AsyncSession = Depends(get_session)
):
    project = await ProjectService.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    project = await ProjectService.update_project(session, project_id, project_in)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID, 
    session: AsyncSession = Depends(get_session)
):
    success = await ProjectService.delete_project(session, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
