"""
SQLAlchemy ORM models for the Industrial Knowledge Intelligence platform.

Tables:
  - documents: uploaded files with extracted metadata
  - chunks: text chunks with pgvector embeddings
  - entities: structured entities extracted from documents
  - relationships: links between entities and documents
  - equipment_failures: mock maintenance/failure records
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    content_text = Column(Text, nullable=True)          # full extracted text
    doc_type = Column(String(100), nullable=True)        # e.g. "maintenance_procedure"
    metadata_json = Column(JSON, nullable=True)          # structured entities as JSON
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(768), nullable=True)       # Gemini text-embedding-004 = 768 dims

    document = relationship("Document", back_populates="chunks")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(100), nullable=False)    # equipment_tag, person, date, regulation, doc_type
    entity_value = Column(String(500), nullable=False)
    raw_context = Column(Text, nullable=True)            # surrounding text where entity was found

    document = relationship("Document", back_populates="entities")
    doc_relationships = relationship("Relationship", back_populates="entity", cascade="all, delete-orphan")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(200), nullable=False)  # e.g. "mentioned_in", "inspected_by"

    entity = relationship("Entity", back_populates="doc_relationships")


class EquipmentFailure(Base):
    __tablename__ = "equipment_failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), nullable=False, index=True)
    failure_date = Column(Date, nullable=False)
    failure_type = Column(String(200), nullable=False)
    root_cause = Column(String(500), nullable=True)
    downtime_hours = Column(Float, nullable=False, default=0.0)


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(200), nullable=False)  # e.g., "associated_with", "inspected_by"
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    source = relationship("Entity", foreign_keys=[source_id])
    target = relationship("Entity", foreign_keys=[target_id])
    document = relationship("Document")


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    regulation_type = Column(String(100), nullable=False)    # Factory Act, OISD, PESO, Environmental
    compliance_score = Column(Integer, nullable=False)       # 0 to 100
    severity_level = Column(String(50), nullable=False)      # Critical, High, Medium, Low
    gap_details = Column(Text, nullable=True)
    corrective_actions = Column(JSON, nullable=True)         # JSON list of strings
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document")


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), nullable=False, index=True)
    incident_date = Column(Date, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    resolutions = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
