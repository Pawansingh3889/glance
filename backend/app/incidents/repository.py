"""Every query the incident form makes."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.runs.models import SurveyRun
from app.templates.models import SurveyTemplateVersion


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_version(self, template_id: UUID) -> SurveyTemplateVersion | None:
        """The newest published version of the incident template. Reports are always
        filed against the current wording, never a superseded one."""
        stmt = (
            select(SurveyTemplateVersion)
            .where(SurveyTemplateVersion.template_id == template_id)
            .order_by(SurveyTemplateVersion.version.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def add(self, run: SurveyRun) -> None:
        self.session.add(run)
