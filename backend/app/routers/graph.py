"""
Graph router — serves Knowledge Graph nodes, edges, and relationship paths.
"""
import logging
import networkx as nx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Entity, EntityRelationship

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/data")
async def get_graph_data(db: AsyncSession = Depends(get_db)):
    """
    Builds and returns graph nodes and edges.
    Nodes are extracted entities, and edges are parsed relationships.
    """
    try:
        # Fetch all entities
        ent_stmt = select(Entity)
        ent_res = await db.execute(ent_stmt)
        entities = ent_res.scalars().all()

        # Fetch all relationships
        rel_stmt = select(EntityRelationship)
        rel_res = await db.execute(rel_stmt)
        relationships = rel_res.scalars().all()

        # Build nodes
        nodes = []
        seen_nodes = set()
        for ent in entities:
            if ent.id not in seen_nodes:
                nodes.append({
                    "id": ent.id,
                    "label": ent.entity_value,
                    "type": ent.entity_type,
                })
                seen_nodes.add(ent.id)

        # Build edges
        edges = []
        for rel in relationships:
            edges.append({
                "id": rel.id,
                "source": rel.source_id,
                "target": rel.target_id,
                "type": rel.relationship_type,
            })

        # Calculate metrics using NetworkX
        g = nx.DiGraph()
        for n in nodes:
            g.add_node(n["id"], label=n["label"], type=n["type"])
        for e in edges:
            g.add_edge(e["source"], e["target"], relationship_type=e["type"])

        density = nx.density(g) if len(nodes) > 0 else 0
        avg_degree = sum(dict(g.degree()).values()) / len(nodes) if len(nodes) > 0 else 0

        # Identify central nodes (highest degree centrality)
        centrality = nx.degree_centrality(g) if len(nodes) > 0 else {}
        sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        top_hubs = []
        for node_id, cent_val in sorted_centrality[:5]:
            node_data = g.nodes[node_id]
            top_hubs.append({
                "id": node_id,
                "label": node_data.get("label", "Unknown"),
                "type": node_data.get("type", "unknown"),
                "score": round(cent_val, 3)
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "density": round(density, 4),
                "average_degree": round(avg_degree, 2),
                "top_hubs": top_hubs
            }
        }

    except Exception as e:
        logger.error(f"Error fetching graph data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph data: {str(e)}")


@router.get("/path")
async def get_shortest_path(
    source_val: str,
    target_val: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Finds the shortest relationship path between two entities by their values.
    """
    try:
        # Resolve entities
        source_ent = (await db.execute(select(Entity).where(Entity.entity_value.ilike(source_val)))).scalars().first()
        target_ent = (await db.execute(select(Entity).where(Entity.entity_value.ilike(target_val)))).scalars().first()

        if not source_ent or not target_ent:
            raise HTTPException(status_code=404, detail="Source or target entity not found")

        # Build graph
        ent_stmt = select(Entity)
        ent_res = await db.execute(ent_stmt)
        entities = ent_res.scalars().all()

        rel_stmt = select(EntityRelationship)
        rel_res = await db.execute(rel_stmt)
        relationships = rel_res.scalars().all()

        g = nx.Graph()  # Undirected for general connectivity
        id_to_value = {ent.id: ent.entity_value for ent in entities}
        id_to_type = {ent.id: ent.entity_type for ent in entities}

        for ent in entities:
            g.add_node(ent.id)
        for rel in relationships:
            g.add_edge(rel.source_id, rel.target_id, type=rel.relationship_type)

        try:
            path_ids = nx.shortest_path(g, source=source_ent.id, target=target_ent.id)
            path_steps = []
            for i in range(len(path_ids)):
                node_id = path_ids[i]
                step = {
                    "id": node_id,
                    "value": id_to_value[node_id],
                    "type": id_to_type[node_id]
                }
                if i < len(path_ids) - 1:
                    edge_data = g.get_edge_data(path_ids[i], path_ids[i+1])
                    step["next_relationship"] = edge_data.get("type", "connected_to")
                path_steps.append(step)

            return {
                "found": True,
                "path": path_steps
            }
        except nx.NetworkNoPath:
            return {
                "found": False,
                "message": f"No relationship path exists between '{source_val}' and '{target_val}'"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing shortest path: {e}")
        raise HTTPException(status_code=500, detail=str(e))
