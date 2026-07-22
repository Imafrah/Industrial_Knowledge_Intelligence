"""
Maintenance Intelligence router — equipment failure analysis with Gemini-powered RCA.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models import EquipmentFailure, Chunk, Document
from app import gemini_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class EquipmentSummary(BaseModel):
    equipment_id: str
    total_failures: int
    total_downtime_hours: float
    last_failure_date: str | None
    last_failure_type: str | None


class MaintenanceAnalysis(BaseModel):
    equipment_id: str
    predictive_flag: str
    risk_level: str
    root_cause_analysis: str
    recommended_actions: list[str]
    next_predicted_failure: str
    confidence: str
    failure_history: list[dict]


@router.get("/equipment", response_model=list[EquipmentSummary])
async def list_equipment(db: AsyncSession = Depends(get_db)):
    """List all equipment with failure summaries."""
    sql = text("""
        SELECT 
            equipment_id,
            COUNT(*) as total_failures,
            SUM(downtime_hours) as total_downtime,
            MAX(failure_date) as last_failure_date,
            (SELECT failure_type FROM equipment_failures ef2 
             WHERE ef2.equipment_id = ef.equipment_id 
             ORDER BY failure_date DESC LIMIT 1) as last_failure_type
        FROM equipment_failures ef
        GROUP BY equipment_id
        ORDER BY total_downtime DESC
    """)
    result = await db.execute(sql)
    rows = result.fetchall()

    return [
        EquipmentSummary(
            equipment_id=row[0],
            total_failures=row[1],
            total_downtime_hours=float(row[2]) if row[2] else 0.0,
            last_failure_date=str(row[3]) if row[3] else None,
            last_failure_type=row[4],
        )
        for row in rows
    ]


@router.get("/analyze/{equipment_id}", response_model=MaintenanceAnalysis)
async def analyze_equipment(equipment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Analyze equipment failure history + related documents with Gemini.
    Returns: predictive flag, RCA, recommended actions.
    """
    # Get failure history
    result = await db.execute(
        select(EquipmentFailure)
        .where(EquipmentFailure.equipment_id == equipment_id)
        .order_by(EquipmentFailure.failure_date.desc())
    )
    failures = result.scalars().all()

    if not failures:
        raise HTTPException(status_code=404, detail=f"No failure records found for {equipment_id}")

    failure_history = [
        {
            "failure_date": str(f.failure_date),
            "failure_type": f.failure_type,
            "root_cause": f.root_cause,
            "downtime_hours": f.downtime_hours,
        }
        for f in failures
    ]

    # Find related documents by searching for equipment_id in chunk text
    related_docs = []
    try:
        sql = text("""
            SELECT DISTINCT d.content_text 
            FROM documents d
            JOIN chunks c ON c.document_id = d.id
            WHERE LOWER(c.content) LIKE :pattern
            LIMIT 3
        """)
        result = await db.execute(sql, {"pattern": f"%{equipment_id.lower()}%"})
        rows = result.fetchall()
        related_docs = [row[0][:2000] for row in rows if row[0]]  # Limit doc length
    except Exception as e:
        logger.warning(f"Error fetching related docs: {e}")

    # Gemini analysis
    analysis = await gemini_client.analyze_maintenance(
        equipment_id=equipment_id,
        failure_history=failure_history,
        related_docs=related_docs,
    )

    return MaintenanceAnalysis(
        equipment_id=equipment_id,
        predictive_flag=analysis.get("predictive_flag", "Watch"),
        risk_level=analysis.get("risk_level", "Medium"),
        root_cause_analysis=analysis.get("root_cause_analysis", "Analysis unavailable"),
        recommended_actions=analysis.get("recommended_actions", []),
        next_predicted_failure=analysis.get("next_predicted_failure", "Unknown"),
        confidence=analysis.get("confidence", "Low"),
        failure_history=failure_history,
    )


class AdvancedAnalysis(BaseModel):
    equipment_id: str
    failure_probability: float
    priority: str
    suggested_spares: list[str]
    recommended_schedule: str
    confidence_score: str
    rationale: str


@router.get("/timeline/{equipment_id}")
async def get_equipment_timeline(equipment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Compiles a chronological history timeline for the specified equipment
    by querying failures and document entities.
    """
    try:
        # 1. Fetch failures
        failures_res = await db.execute(
            select(EquipmentFailure)
            .where(EquipmentFailure.equipment_id == equipment_id)
            .order_by(EquipmentFailure.failure_date.asc())
        )
        failures = failures_res.scalars().all()

        timeline = []
        for f in failures:
            timeline.append({
                "date": str(f.failure_date),
                "event_type": "Repair & Failure",
                "title": f.failure_type,
                "description": f.root_cause or "No root cause recorded.",
                "impact": f"{f.downtime_hours}h downtime",
                "severity": "High" if f.downtime_hours > 24 else "Medium"
            })

        # 2. Fetch documents referencing this equipment tag
        doc_stmt = text("""
            SELECT DISTINCT d.id, d.filename, d.doc_type, d.created_at, d.metadata_json
            FROM documents d
            JOIN entities e ON e.document_id = d.id
            WHERE e.entity_type = 'equipment_tag' AND LOWER(e.entity_value) = :eq_id
        """)
        doc_res = await db.execute(doc_stmt, {"eq_id": equipment_id.lower()})
        docs = doc_res.fetchall()

        for doc in docs:
            doc_id, filename, doc_type, created_at, metadata = doc
            event_type = "Procedure Reference"
            severity = "Low"
            if doc_type == "safety_inspection":
                event_type = "Safety Inspection"
                severity = "Medium"
            elif doc_type == "regulatory_checklist":
                event_type = "Compliance Audit"
                severity = "Medium"
            elif doc_type == "incident_report":
                event_type = "Incident Report"
                severity = "High"
            elif doc_type == "equipment_manual":
                event_type = "Specs & Manuals"
                severity = "Low"

            # Use dates from metadata, fallback to created_at
            dates = metadata.get("dates", []) if metadata else []
            event_date = dates[0] if dates else str(created_at.date())

            timeline.append({
                "date": event_date,
                "event_type": event_type,
                "title": f"Referenced in {filename}",
                "description": metadata.get("summary", "Document referenced this equipment tag.") if metadata else "Referenced in documents.",
                "impact": f"Doc ID: {doc_id}",
                "severity": severity
            })

        # Sort chronologically by date
        timeline = sorted(timeline, key=lambda x: x["date"])
        return timeline

    except Exception as e:
        logger.error(f"Error compiling timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced-analysis/{equipment_id}", response_model=AdvancedAnalysis)
async def get_advanced_analysis(equipment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate advanced predictive maintenance insights (priority, fail probability, spares, schedule)
    using Gemini.
    """
    try:
        # Fetch failures
        result = await db.execute(
            select(EquipmentFailure)
            .where(EquipmentFailure.equipment_id == equipment_id)
            .order_by(EquipmentFailure.failure_date.desc())
        )
        failures = result.scalars().all()

        if not failures:
            raise HTTPException(status_code=404, detail=f"No failure records found for {equipment_id}")

        failures_json = [
            {
                "date": str(f.failure_date),
                "type": f.failure_type,
                "cause": f.root_cause,
                "downtime": f.downtime_hours
            }
            for f in failures
        ]

        # Fetch related document segments
        doc_stmt = text("""
            SELECT DISTINCT d.content_text
            FROM documents d
            JOIN entities e ON e.document_id = d.id
            WHERE e.entity_type = 'equipment_tag' AND LOWER(e.entity_value) = :eq_id
            LIMIT 3
        """)
        doc_res = await db.execute(doc_stmt, {"eq_id": equipment_id.lower()})
        docs = doc_res.fetchall()
        docs_text = "\n\n".join([d[0][:1500] for d in docs]) if docs else "No specific manuals or reports found."

        analysis = await gemini_client.generate_advanced_maintenance(failures_json, docs_text)

        return AdvancedAnalysis(
            equipment_id=equipment_id,
            failure_probability=float(analysis.get("failure_probability", 50.0)),
            priority=analysis.get("priority", "Medium"),
            suggested_spares=analysis.get("suggested_spares", []),
            recommended_schedule=analysis.get("recommended_schedule", "Check during next turnaround"),
            confidence_score=analysis.get("confidence_score", "Low"),
            rationale=analysis.get("rationale", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compiling advanced maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
