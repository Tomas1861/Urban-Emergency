"""GraphRAG 轻量版：用 Neo4j 存储从知识文档中抽取的实体与关系，
提供图谱可视化数据与"先查图谱、再取关联文本"的基础检索。

与 HazmatAI_v2 等其他项目共用同一台 Neo4j 时，请通过 NEO4J_DATABASE 指向
独立的数据库，避免数据混在一起（Neo4j 企业版支持同实例多数据库）。
"""
from neo4j import GraphDatabase

from app.core.config import get_settings


class GraphService:
    def __init__(self):
        settings = get_settings()
        self._driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        self._database = settings.neo4j_database

    def close(self):
        self._driver.close()

    def verify_connectivity(self) -> bool:
        self._driver.verify_connectivity()
        return True

    def upsert_entity(self, *, name: str, entity_type: str, description: str, document_id: str, chunk_id: str):
        with self._driver.session(database=self._database) as session:
            session.run(
                """
                MERGE (e:Entity {name: $name})
                ON CREATE SET e.type = $entity_type, e.description = $description
                ON MATCH SET e.description = CASE WHEN size($description) > size(coalesce(e.description, ''))
                    THEN $description ELSE e.description END
                MERGE (e)-[:MENTIONED_IN]->(c:Chunk {id: $chunk_id})
                SET c.document_id = $document_id
                """,
                name=name,
                entity_type=entity_type,
                description=description,
                document_id=document_id,
                chunk_id=chunk_id,
            )

    def upsert_relationship(self, *, source: str, target: str, rel_type: str, description: str):
        with self._driver.session(database=self._database) as session:
            session.run(
                """
                MERGE (a:Entity {name: $source})
                MERGE (b:Entity {name: $target})
                MERGE (a)-[r:RELATES_TO {type: $rel_type}]->(b)
                SET r.description = $description
                """,
                source=source,
                target=target,
                rel_type=rel_type,
                description=description,
            )

    def clear_document(self, document_id: str):
        with self._driver.session(database=self._database) as session:
            session.run(
                """
                MATCH (c:Chunk {document_id: $document_id})
                DETACH DELETE c
                """,
                document_id=document_id,
            )
            session.run(
                """
                MATCH (e:Entity) WHERE NOT (e)-[:MENTIONED_IN]->(:Chunk)
                DETACH DELETE e
                """
            )

    def get_graph(self, *, document_id: str | None = None, limit: int = 300) -> dict:
        with self._driver.session(database=self._database) as session:
            if document_id:
                result = session.run(
                    """
                    MATCH (e:Entity)-[:MENTIONED_IN]->(c:Chunk {document_id: $document_id})
                    WITH collect(DISTINCT e) AS es
                    UNWIND es AS e
                    OPTIONAL MATCH (e)-[r:RELATES_TO]-(o:Entity) WHERE o IN es
                    RETURN e, collect(DISTINCT {rel: r, other: o}) AS rels
                    LIMIT $limit
                    """,
                    document_id=document_id,
                    limit=limit,
                )
            else:
                result = session.run(
                    """
                    MATCH (e:Entity)
                    OPTIONAL MATCH (e)-[r:RELATES_TO]->(o:Entity)
                    RETURN e, collect(DISTINCT {rel: r, other: o}) AS rels
                    LIMIT $limit
                    """,
                    limit=limit,
                )
            nodes: dict[str, dict] = {}
            edges: list[dict] = []
            for record in result:
                e = record["e"]
                nodes[e["name"]] = {"id": e["name"], "type": e.get("type", ""), "description": e.get("description", "")}
                for item in record["rels"]:
                    if item["other"] is None:
                        continue
                    other = item["other"]
                    nodes[other["name"]] = {
                        "id": other["name"],
                        "type": other.get("type", ""),
                        "description": other.get("description", ""),
                    }
                    rel = item["rel"]
                    edges.append({
                        "source": e["name"],
                        "target": other["name"],
                        "type": rel.get("type", ""),
                        "description": rel.get("description", ""),
                    })
            return {"nodes": list(nodes.values()), "edges": edges}

    def search_entities(self, query: str, *, limit: int = 10) -> list[dict]:
        with self._driver.session(database=self._database) as session:
            result = session.run(
                """
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower($query) OR toLower(coalesce(e.description,'')) CONTAINS toLower($query)
                OPTIONAL MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
                RETURN e.name AS name, e.type AS type, e.description AS description, collect(DISTINCT c.id) AS chunk_ids
                LIMIT $limit
                """,
                query=query,
                limit=limit,
            )
            return [dict(r) for r in result]

    def stats(self) -> dict:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (e:Entity) WITH count(e) AS entities
                MATCH ()-[r:RELATES_TO]->() WITH entities, count(r) AS relationships
                MATCH (c:Chunk) WITH entities, relationships, count(DISTINCT c.document_id) AS documents
                RETURN entities, relationships, documents
                """
            ).single()
            if record is None:
                return {"entities": 0, "relationships": 0, "documents": 0}
            return dict(record)
