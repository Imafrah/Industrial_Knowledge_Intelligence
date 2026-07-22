"""
Compliance Intelligence router — provides endpoints for audits, gaps, scores, and safety compliance lists.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models import ComplianceFinding, Document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compliance", tags=["compliance"])


class ComplianceSummary(BaseModel):
    average_score: float
    total_audits: int
    critical_gaps_count: int
    high_gaps_count: int
    medium_gaps_count: int
    low_gaps_count: int
    status: str


class FindingDetail(BaseModel):
    id: int
    document_id: int
    filename: str
    regulation_type: str
    compliance_score: int
    severity_level: str
    gap_details: str | None
    corrective_actions: list[str] | None
    created_at: str


@router.get("/summary", response_model=ComplianceSummary)
async def get_compliance_summary(db: AsyncSession = Depends(get_db)):
    """
    Returns global compliance summary metrics: average score, gap counts by severity.
    """
    try:
        # Get count of findings
        count_stmt = select(func.count()).select_from(ComplianceFinding)
        total_audits = (await db.execute(count_stmt)).scalar() or 0

        if total_audits == 0:
            return ComplianceSummary(
                average_score=100.0,
                total_audits=0,
                critical_gaps_count=0,
                high_gaps_count=0,
                medium_gaps_count=0,
                low_gaps_count=0,
                status="Compliant"
            )

        # Get average score
        avg_stmt = select(func.avg(ComplianceFinding.compliance_score)).select_from(ComplianceFinding)
        avg_score = float((await db.execute(avg_stmt)).scalar() or 100.0)

        # Get breakdown by severity
        breakdown_sql = text("""
            SELECT severity_level, COUNT(*) 
            FROM compliance_findings 
            GROUP BY severity_level
        """)
        breakdown_res = await db.execute(breakdown_sql)
        breakdown = dict(breakdown_res.fetchall())

        critical_gaps = breakdown.get("Critical", 0)
        high_gaps = breakdown.get("High", 0)
        medium_gaps = breakdown.get("Medium", 0)
        low_gaps = breakdown.get("Low", 0)

        # Determine overall safety status
        if critical_gaps > 0:
            status = "ACTION REQUIRED (CRITICAL GAPS)"
        elif high_gaps > 0:
            status = "WARNING (HIGH RISK GAPS)"
        elif avg_score < 80:
            status = "ATTENTION REQUIRED"
        else:
            status = "COMPLIANT"

        return ComplianceSummary(
            average_score=round(avg_score, 1),
            total_audits=total_audits,
            critical_gaps_count=critical_gaps,
            high_gaps_count=high_gaps,
            medium_gaps_count=medium_gaps,
            low_gaps_count=low_gaps,
            status=status
        )

    except Exception as e:
        logger.error(f"Error fetching compliance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/findings", response_model=list[FindingDetail])
async def get_compliance_findings(db: AsyncSession = Depends(get_db)):
    """
    Returns all compliance findings with details and linked documents.
    """
    try:
        stmt = (
            select(
                ComplianceFinding.id,
                ComplianceFinding.document_id,
                Document.filename,
                ComplianceFinding.regulation_type,
                ComplianceFinding.compliance_score,
                ComplianceFinding.severity_level,
                ComplianceFinding.gap_details,
                ComplianceFinding.corrective_actions,
                ComplianceFinding.created_at
            )
            .join(Document, ComplianceFinding.document_id == Document.id)
            .order_by(ComplianceFinding.created_at.desc())
        )
        res = await db.execute(stmt)
        rows = res.all()

        return [
            FindingDetail(
                id=row[0],
                document_id=row[1],
                filename=row[2],
                regulation_type=row[3],
                compliance_score=row[4],
                severity_level=row[5],
                gap_details=row[6],
                corrective_actions=row[7],
                created_at=str(row[8])
            )
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error fetching compliance findings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
