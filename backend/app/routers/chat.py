"""
Chat router — RAG-powered question answering with citations and confidence scoring.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app import gemini_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class SourceCitation(BaseModel):
    filename: str
    excerpt: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    confidence: str  # High, Medium, Low


def compute_confidence(similarities: list[float]) -> str:
    """
    Derive confidence from average cosine similarity of top retrieved chunks.
    """
    if not similarities:
        return "Low"
    avg = sum(similarities) / len(similarities)
    if avg >= 0.75:
        return "High"
    elif avg >= 0.55:
        return "Medium"
    else:
        return "Low"


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    RAG chat endpoint:
    1. Embed the user's question
    2. Retrieve top-5 most similar chunks from pgvector
    3. Pass chunks + question to Gemini for answer generation
    4. Return answer with source citations and confidence score
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Step 1: Embed the question
        query_embedding = await gemini_client.generate_query_embedding(request.question)

        # Step 2: Vector similarity search — top 5 chunks
        # pgvector cosine distance: 1 - cosine_similarity, so we ORDER BY ascending
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        sql = text("""
            SELECT 
                c.content,
                c.chunk_index,
                d.filename,
                1 - (c.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT 5
        """)
        result = await db.execute(sql, {"embedding": embedding_str})
        rows = result.fetchall()

        if not rows:
            return ChatResponse(
                answer="I don't have any documents in my knowledge base yet. Please upload some documents first.",
                sources=[],
                confidence="Low",
            )

        # Step 3: Prepare context and generate answer
        context_chunks = []
        sources = []
        similarities = []

        for row in rows:
            content, chunk_idx, filename, similarity = row
            context_chunks.append({
                "content": content,
                "filename": filename,
                "similarity": float(similarity),
            })
            sources.append(SourceCitation(
                filename=filename,
                excerpt=content[:300] + ("..." if len(content) > 300 else ""),
                similarity=round(float(similarity), 3),
            ))
            similarities.append(float(similarity))

        answer = await gemini_client.generate_answer(request.question, context_chunks)
        confidence = compute_confidence(similarities)

        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
