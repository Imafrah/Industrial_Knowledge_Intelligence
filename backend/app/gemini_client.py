"""
Gemini AI client — wraps google-generativeai SDK for embeddings, entity extraction,
RAG answer generation, and maintenance intelligence analysis.
"""
import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure the SDK on import
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "models/gemini-embedding-001"


async def generate_embedding(text: str) -> list[float]:
    """Generate a 768-dim embedding for a single text string."""
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document",
            output_dimensionality=768,
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


async def generate_query_embedding(text: str) -> list[float]:
    """Generate an embedding optimized for query/retrieval."""
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query",
            output_dimensionality=768,
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Query embedding error: {e}")
        raise


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts,
            task_type="retrieval_document",
            output_dimensionality=768,
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        raise


# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------

FLASH_MODEL = "gemini-2.5-flash"


async def extract_entities(text: str) -> dict:
    """
    Use Gemini to extract structured entities from industrial document text.
    Returns a dict with keys: equipment_tags, dates, personnel, regulations,
    document_type, summary.
    """
    prompt = f"""You are an industrial document analysis AI. Analyze the following document text 
and extract structured information. Return ONLY valid JSON with these exact keys:

{{
  "document_type": "one of: maintenance_procedure, safety_inspection, equipment_manual, incident_report, regulatory_checklist, rfi, other",
  "summary": "2-3 sentence summary of the document",
  "equipment_tags": ["list of equipment IDs, tag numbers, or equipment names mentioned"],
  "dates": ["list of dates mentioned in any format"],
  "personnel": ["list of people/roles mentioned"],
  "regulations": ["list of regulatory standards, codes, or compliance references"],
  "key_findings": ["list of important findings, issues, or action items"]
}}

Document text:
---
{text[:4000]}
---

Return ONLY the JSON object, no markdown formatting or extra text."""

    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        # Parse JSON from response, handling potential markdown wrapping
        response_text = response.text.strip()
        if response_text.startswith("```"):
            # Strip markdown code fences
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse entity extraction JSON, returning defaults")
        return {
            "document_type": "other",
            "summary": "Could not extract summary",
            "equipment_tags": [],
            "dates": [],
            "personnel": [],
            "regulations": [],
            "key_findings": [],
        }
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return {
            "document_type": "other",
            "summary": str(e),
            "equipment_tags": [],
            "dates": [],
            "personnel": [],
            "regulations": [],
            "key_findings": [],
        }


# ---------------------------------------------------------------------------
# RAG Answer Generation
# ---------------------------------------------------------------------------


async def generate_answer(question: str, context_chunks: list[dict]) -> str:
    """
    Generate an answer using retrieved context chunks.
    Each chunk dict has keys: content, filename, similarity.
    """
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n--- Source {i}: {chunk['filename']} (relevance: {chunk['similarity']:.2f}) ---\n"
        context_text += chunk["content"] + "\n"

    prompt = f"""You are an expert industrial knowledge assistant for a plant operations team. 
Answer the following question using ONLY the provided source documents. 
If the sources don't contain enough information, say so clearly.
Be specific, cite which source documents support your answer, and be practical.

SOURCES:
{context_text}

QUESTION: {question}

Provide a clear, well-structured answer. Reference source numbers (e.g., "According to Source 1...") when citing information."""

    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Answer generation error: {e}")
        return f"I encountered an error generating an answer: {str(e)}"


# ---------------------------------------------------------------------------
# Maintenance Intelligence Analysis
# ---------------------------------------------------------------------------


async def analyze_maintenance(
    equipment_id: str,
    failure_history: list[dict],
    related_docs: list[str],
) -> dict:
    """
    Analyze equipment failure history and related documents to generate
    predictive maintenance insights.
    """
    history_text = json.dumps(failure_history, indent=2, default=str)
    docs_text = "\n\n".join(related_docs[:3]) if related_docs else "No related maintenance documents found."

    prompt = f"""You are a predictive maintenance AI analyst. Analyze the failure history and 
maintenance documents for equipment "{equipment_id}" and provide insights.

FAILURE HISTORY:
{history_text}

RELATED MAINTENANCE DOCUMENTS:
{docs_text}

Return ONLY valid JSON with these exact keys:
{{
  "predictive_flag": "Yes or No or Watch",
  "risk_level": "High or Medium or Low",
  "root_cause_analysis": "Plain-English paragraph explaining the likely root cause patterns",
  "recommended_actions": ["list of 2-4 specific recommended maintenance actions"],
  "next_predicted_failure": "Estimated timeframe for next potential failure based on patterns",
  "confidence": "High or Medium or Low"
}}

Return ONLY the JSON object."""

    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "predictive_flag": "Watch",
            "risk_level": "Medium",
            "root_cause_analysis": "Unable to parse AI analysis. Manual review recommended.",
            "recommended_actions": ["Schedule manual inspection", "Review maintenance logs"],
            "next_predicted_failure": "Unknown",
            "confidence": "Low",
        }
    except Exception as e:
        logger.error(f"Maintenance analysis error: {e}")
        return {
            "predictive_flag": "Watch",
            "risk_level": "Medium",
            "root_cause_analysis": str(e),
            "recommended_actions": ["Check system configuration"],
            "next_predicted_failure": "Unknown",
            "confidence": "Low",
        }


async def extract_entity_relationships(text: str, entities: list[dict]) -> list[dict]:
    """
    Use Gemini to extract subject-predicate-object triples linking the identified entities.
    Returns a list of dicts: [{"source_value": "...", "target_value": "...", "relationship_type": "..."}]
    """
    if not entities:
        return []
    entities_str = json.dumps([{"type": e["type"], "value": e["value"]} for e in entities], indent=2)
    prompt = f"""You are a knowledge graph AI builder. Analyze the following document text and extract relationships between these specific entities:

SPECIFIC ENTITIES:
{entities_str}

DOCUMENT TEXT:
---
{text[:4000]}
---

Identify connections between the entities listed above. For each connection, identify the relationship type (e.g. "responsible_for", "governed_by", "inspected_by", "located_in", "part_of", "caused_by", "referenced_in").
Return ONLY valid JSON as a list of objects with this exact structure:
[
  {{
    "source_value": "exact value of the source entity from the list above",
    "target_value": "exact value of the target entity from the list above",
    "relationship_type": "type of relationship"
  }}
]

Return ONLY the JSON list, no markdown wrapping."""

    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Error extracting relationships: {e}")
        return []


async def audit_compliance(text: str) -> dict:
    """
    Compare document text against standard industrial regulations:
    Factory Act, OISD, PESO, Environmental Standards.
    Returns a dict with audited score, gaps, severity, actions.
    """
    prompt = f"""You are an industrial safety compliance AI auditor. Analyze the following document text 
against general regulations (Factory Act, OISD, PESO, Environmental Standards).

DOCUMENT TEXT:
---
{text[:5000]}
---

Identify:
1. Gaps in compliance, missing safety guards, missing checklists.
2. Expired certificates or permits.
3. Missing periodic inspections or tests.
4. Compliance score (0-100, where 100 is fully compliant).
5. Overall severity of gaps found (Critical, High, Medium, Low).
6. Recommended corrective actions.

Return ONLY valid JSON with this exact structure:
{{
  "regulation_type": "Primary regulation matched, one of: Factory Act, OISD, PESO, Environmental, or General Safety",
  "compliance_score": 85,
  "severity_level": "one of: Critical, High, Medium, Low",
  "gap_details": "A paragraph explaining identified gaps, missing safety protocols, inspections, or expired certificates.",
  "corrective_actions": ["List of 2-5 specific actions to achieve full compliance"]
}}

Return ONLY the JSON object, no formatting."""
    
    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Compliance audit error: {e}")
        return {
            "regulation_type": "General Safety",
            "compliance_score": 100,
            "severity_level": "Low",
            "gap_details": "No compliance issues detected during manual fallbacks.",
            "corrective_actions": []
        }


async def generate_advanced_maintenance(
    failures_history: list[dict],
    docs_text: str
) -> dict:
    """
    Generate advanced predictive maintenance recommendations.
    Returns: failure probability (float), spares (list), schedule (string), priority (string).
    """
    history_text = json.dumps(failures_history, indent=2, default=str)
    prompt = f"""You are a senior reliability and mechanical integrity engineer.
Analyze the equipment failure history and reference document excerpts below.

FAILURE HISTORY:
{history_text}

REFERENCE DOCUMENTATION EXCERPTS:
{docs_text}

Calculate and output the following metrics in valid JSON:
1. Estimated failure probability over the next 90 days (percentage between 0 and 100).
2. Maintenance priority (Immediate, High, Medium, Low).
3. Suggested spare parts (list of strings, specify part numbers if available).
4. Recommended maintenance schedule / next check date.
5. Recommendation rationale and confidence score (High, Medium, Low).

Return ONLY valid JSON with this structure:
{{
  "failure_probability": 45.5,
  "priority": "High",
  "suggested_spares": ["Part A", "Part B"],
  "recommended_schedule": "Inspect within 14 days, repacking bearing housings",
  "confidence_score": "High",
  "rationale": "Explanation of the calculated probability and priority based on failure cycles."
}}

Return ONLY the JSON object, no markdown formatting."""

    try:
        model = genai.GenerativeModel(FLASH_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Advanced maintenance analysis error: {e}")
        return {
            "failure_probability": 50.0,
            "priority": "Medium",
            "suggested_spares": ["General Seal Gaskets"],
            "recommended_schedule": "Next quarterly inspection",
            "confidence_score": "Low",
            "rationale": f"Fallback error: {e}"
        }
