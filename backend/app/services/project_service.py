from typing import List, Optional
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project, ProjectCreate, ProjectUpdate

class ProjectService:
    @staticmethod
    async def create_project(session: AsyncSession, project_in: ProjectCreate) -> Project:
        db_project = Project.from_orm(project_in)
        session.add(db_project)
        await session.commit()
        await session.refresh(db_project)
        return db_project

    @staticmethod
    async def get_project(session: AsyncSession, project_id: UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_projects(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        statement = select(Project).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def update_project(
        session: AsyncSession, project_id: UUID, project_in: ProjectUpdate
    ) -> Optional[Project]:
        db_project = await ProjectService.get_project(session, project_id)
        if not db_project:
            return None
        
        project_data = project_in.dict(exclude_unset=True)
        for key, value in project_data.items():
            setattr(db_project, key, value)
        
        session.add(db_project)
        await session.commit()
        await session.refresh(db_project)
        return db_project

    @staticmethod
    async def delete_project(session: AsyncSession, project_id: UUID) -> bool:
        db_project = await ProjectService.get_project(session, project_id)
        if not db_project:
            return False
        
        await session.delete(db_project)
        await session.commit()
        return True
