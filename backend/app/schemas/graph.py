"""GraphRAG 轻量版 Schema：实体/关系抽取Agent的输出结构。"""
from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    name: str
    type: str
    description: str = ""


class ExtractedRelationship(BaseModel):
    source: str
    target: str
    type: str
    description: str = ""


class EntityExtractionOutput(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    type: str = ""
    description: str = ""


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str = ""
    description: str = ""


class GraphData(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class GraphSearchResult(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    chunk_ids: list[str] = Field(default_factory=list)


class GraphStats(BaseModel):
    entities: int = 0
    relationships: int = 0
    documents: int = 0
