"""
Dashboard router — stats and recent documents for the home page.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.database import get_db
from app.models import Document, Entity, Chunk, ComplianceFinding, EntityRelationship

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_documents: int
    total_entities: int
    total_chunks: int
    avg_compliance_score: float
    graph_relationships: int


class RecentDocument(BaseModel):
    id: int
    filename: str
    doc_type: str | None
    chunk_count: int
    entity_count: int
    created_at: str


class HighRiskEquipment(BaseModel):
    equipment_id: str
    failures: int
    downtime_hours: float
    risk_status: str


class UpcomingInspection(BaseModel):
    equipment_id: str
    type: str
    due_date: str
    assigned_to: str


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_documents: list[RecentDocument]
    high_risk_equipment: list[HighRiskEquipment]
    upcoming_inspections: list[UpcomingInspection]


@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Return aggregate stats and recent documents for the dashboard."""
    # Count totals
    doc_count = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    entity_count = (await db.execute(select(func.count()).select_from(Entity))).scalar() or 0
    chunk_count = (await db.execute(select(func.count()).select_from(Chunk))).scalar() or 0
    
    comp_score = (await db.execute(select(func.avg(ComplianceFinding.compliance_score)))).scalar()
    avg_compliance = float(comp_score) if comp_score is not None else 85.0
    
    graph_rels = (await db.execute(select(func.count()).select_from(EntityRelationship))).scalar() or 0

    stats = DashboardStats(
        total_documents=doc_count,
        total_entities=entity_count,
        total_chunks=chunk_count,
        avg_compliance_score=round(avg_compliance, 1),
        graph_relationships=graph_rels
    )

    # Recent documents with entity counts
    result = await db.execute(
        select(
            Document.id,
            Document.filename,
            Document.doc_type,
            Document.chunk_count,
            func.count(Entity.id).label("entity_count"),
            Document.created_at,
        )
        .outerjoin(Entity, Entity.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
        .limit(10)
    )
    rows = result.all()

    recent_documents = [
        RecentDocument(
            id=row[0],
            filename=row[1],
            doc_type=row[2] or "unknown",
            chunk_count=row[3] or 0,
            entity_count=row[4],
            created_at=str(row[5]) if row[5] else "",
        )
        for row in rows
    ]

    # Fetch high-risk equipment based on failures and downtime
    risk_stmt = text("""
        SELECT equipment_id, COUNT(*) as fail_count, SUM(downtime_hours) as total_downtime
        FROM equipment_failures
        GROUP BY equipment_id
        ORDER BY total_downtime DESC
        LIMIT 5
    """)
    risk_res = await db.execute(risk_stmt)
    risk_rows = risk_res.fetchall()
    
    high_risk_equipment = [
        HighRiskEquipment(
            equipment_id=row[0],
            failures=row[1],
            downtime_hours=float(row[2]) if row[2] else 0.0,
            risk_status="High" if (row[2] and row[2] > 25) else "Medium"
        )
        for row in risk_rows
    ]

    # Fetch upcoming inspection dates (seeded mock list)
    upcoming_inspections = [
        UpcomingInspection(equipment_id="P-101A", type="Quarterly PM Alignment", due_date="2026-08-15", assigned_to="John Martinez"),
        UpcomingInspection(equipment_id="DS-03", type="NFPA Flow Re-testing", due_date="2026-07-26", assigned_to="David Kim"),
        UpcomingInspection(equipment_id="HX-201", type="Shell & Tube Hydrostatic Test", due_date="2026-09-01", assigned_to="Sarah Chen")
    ]

    return DashboardResponse(
        stats=stats, 
        recent_documents=recent_documents,
        high_risk_equipment=high_risk_equipment,
        upcoming_inspections=upcoming_inspections
    )
