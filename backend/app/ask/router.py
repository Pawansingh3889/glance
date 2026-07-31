"""Ask routes. Thin: resolve the user, call one service method, return its result."""

from fastapi import APIRouter, Depends

from app.ask.schemas import AskAnswer, AskRequest
from app.ask.service import AskService
from app.auth.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/api/v1/ask", tags=["ask"])


@router.post("", response_model=AskAnswer)
async def ask(
    data: AskRequest,
    # Any signed-in role: an operative asking about glove policy and a technical manager
    # asking about verification frequency want the same service. Gated rather than open
    # because every call spends provider tokens.
    _user: User = Depends(get_current_user),
) -> AskAnswer:
    return await AskService().ask(data.question, data.language)
