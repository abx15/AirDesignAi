from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Equation, User
from schemas import EquationCreate, EquationRead
from utils import get_current_user


router = APIRouter(prefix="/equations", tags=["equations"])


@router.post("/", response_model=EquationRead, status_code=status.HTTP_201_CREATED)
async def save_equation(
    payload: EquationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquationRead:
    equation = Equation(
        user_id=current_user.id,
        expression=payload.expression,
        solution=payload.solution,
        steps=payload.steps,
        graph_data=payload.graph_data,
        confidence=payload.confidence,
    )
    db.add(equation)
    await db.commit()
    await db.refresh(equation)
    return equation


@router.get("/history", response_model=List[EquationRead])
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EquationRead]:
    stmt = select(Equation).where(Equation.user_id == current_user.id).order_by(Equation.created_at.desc())
    result = await db.execute(stmt)
    equations = result.scalars().all()
    return equations


@router.delete("/{equation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equation(
    equation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    stmt = delete(Equation).where(Equation.id == equation_id, Equation.user_id == current_user.id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Equation not found")
    await db.commit()

