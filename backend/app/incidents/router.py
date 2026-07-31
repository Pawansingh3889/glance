"""Incident routes. Thin: resolve the reporter, call one service method, return it."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.incidents.schemas import IncidentForm, IncidentReceipt, IncidentSubmission
from app.incidents.service import IncidentService
from app.users.models import User

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.get("/form", response_model=IncidentForm)
async def incident_form(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentForm:
    """The fields to render, straight from the published template version."""
    return await IncidentService(session).form()


@router.post("", response_model=IncidentReceipt, status_code=HTTP_201_CREATED)
async def file_incident(
    data: IncidentSubmission,
    # Any signed-in role, not participants only: a line leader or a technical manager
    # finding an unsafe condition has to be able to file it too, and require_participant
    # would refuse them.
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentReceipt:
    return await IncidentService(session).submit(data.answers, user)
