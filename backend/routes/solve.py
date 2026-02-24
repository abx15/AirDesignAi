from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import SolveRequest, SolveResponse
from services.ocr import ocr_service
from services.solver import solver_service
from utils import get_current_user
from models import User


router = APIRouter(prefix="/solve", tags=["solve"])


_RATE_LIMIT_BUCKET: dict[str, list[float]] = {}
_MAX_CALLS = 30
_WINDOW_SECONDS = 60.0


def _rate_limit(user_identifier: str, now: float) -> None:
    import time

    window_start = now - _WINDOW_SECONDS
    bucket = _RATE_LIMIT_BUCKET.setdefault(user_identifier, [])
    # purge old
    bucket[:] = [t for t in bucket if t >= window_start]
    if len(bucket) >= _MAX_CALLS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down.",
        )
    bucket.append(now)


@router.post("/", response_model=SolveResponse)
async def solve_equation(
    payload: SolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SolveResponse:
    import time

    _ = db  # currently unused but kept for future persistence hooks

    _rate_limit(str(current_user.id), time.time())

    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="Image is required")

    # OCR
    latex, confidence = await ocr_service.extract_math_from_image(payload.image_base64)
    if not latex:
        raise HTTPException(status_code=422, detail="Unable to read equation")

    # Basic validation / sanitization: SymPy will reject unsafe content; we
    # also forbid certain characters.
    if any(bad in latex for bad in ["__", "import", "exec", "lambda"]):
        raise HTTPException(status_code=400, detail="Invalid expression content")

    # Solve generically; in a more advanced setup you'd branch by detected type.
    try:
        solution_latex, steps = solver_service.solve_generic(latex)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not solve expression: {exc}")

    # Graph data (best-effort)
    graph_data = None
    try:
        graph_data = solver_service.build_graph_data(latex)
    except Exception:
        graph_data = None

    # If confidence low, client can show suggestion UI
    return SolveResponse(
        expression=latex,
        solution=solution_latex,
        steps=steps,
        graph_data=graph_data,
        confidence=confidence,
    )

