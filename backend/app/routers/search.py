"""
Hybrid Search router — merges vector similarity search and keyword lexical search
using Reciprocal Rank Fusion (RRF) with metadata filtering.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app import gemini_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


class HybridSearchRequest(BaseModel):
    query: str
    doc_type: str | None = None
    equipment_tag: str | None = None
    limit: int = 10


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    doc_type: str | None
    content: str
    score: float  # Hybrid RRF score
    rank: int
    search_method: str  # "Vector Only", "Keyword Only", or "Hybrid"


@router.post("/hybrid", response_model=list[SearchResult])
async def hybrid_search(request: HybridSearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Performs Hybrid Search (Vector + Keyword) with optional metadata filtering:
    1. Runs semantic vector search on chunks
    2. Runs ILIKE lexical search on chunks
    3. Merges and ranks results using Reciprocal Rank Fusion (RRF)
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        # Step 1: Run Vector Search (Semantic)
        query_embedding = await gemini_client.generate_query_embedding(request.query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Metadata filters
        where_clauses = ["c.embedding IS NOT NULL"]
        params = {"embedding": embedding_str, "query": f"%{request.query.lower()}%"}

        if request.doc_type:
            where_clauses.append("d.doc_type = :doc_type")
            params["doc_type"] = request.doc_type

        if request.equipment_tag:
            # Check if chunk mentions the equipment tag (case-insensitive)
            where_clauses.append("LOWER(c.content) LIKE :equipment_tag")
            params["equipment_tag"] = f"%{request.equipment_tag.lower()}%"

        where_str = " AND ".join(where_clauses)

        vector_sql = text(f"""
            SELECT 
                c.id, c.document_id, d.filename, d.doc_type, c.content,
                1 - (c.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE {where_str}
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT 50
        """)
        vector_res = await db.execute(vector_sql, params)
        vector_rows = vector_res.fetchall()

        # Step 2: Run Keyword Search (Lexical matching via LIKE)
        # We reuse the same filters, but perform string matching on query terms
        keyword_where = where_clauses.copy()
        # Remove embedding distance requirement for keyword if not needed, but keep chunks filtered
        keyword_where = [clause for clause in keyword_where if "embedding" not in clause]
        keyword_where.append("LOWER(c.content) LIKE :query")

        keyword_where_str = " AND ".join(keyword_where)

        keyword_sql = text(f"""
            SELECT 
                c.id, c.document_id, d.filename, d.doc_type, c.content,
                1.0 as relevance
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE {keyword_where_str}
            LIMIT 50
        """)
        keyword_res = await db.execute(keyword_sql, params)
        keyword_rows = keyword_res.fetchall()

        # Step 3: Reciprocal Rank Fusion (RRF)
        # RRF score = sum(1 / (k + rank)) for each list, constant k = 60
        k = 60
        rrf_scores = {}
        chunk_details = {}
        sources = {}

        # Process vector ranks (1-indexed)
        for rank, row in enumerate(vector_rows, 1):
            c_id, doc_id, filename, doc_type, content, sim = row
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k + rank))
            chunk_details[c_id] = (doc_id, filename, doc_type, content)
            sources[c_id] = sources.get(c_id, set())
            sources[c_id].add("Vector")

        # Process keyword ranks (1-indexed)
        for rank, row in enumerate(keyword_rows, 1):
            c_id, doc_id, filename, doc_type, content, rel = row
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k + rank))
            chunk_details[c_id] = (doc_id, filename, doc_type, content)
            sources[c_id] = sources.get(c_id, set())
            sources[c_id].add("Keyword")

        # Sort by RRF score descending
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for idx, (c_id, score) in enumerate(sorted_chunks[:request.limit], 1):
            doc_id, filename, doc_type, content = chunk_details[c_id]
            method = "Hybrid" if len(sources[c_id]) > 1 else list(sources[c_id])[0] + " Only"
            results.append(SearchResult(
                chunk_id=c_id,
                document_id=doc_id,
                filename=filename,
                doc_type=doc_type,
                content=content,
                score=round(score, 5),
                rank=idx,
                search_method=method
            ))

        return results

    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
