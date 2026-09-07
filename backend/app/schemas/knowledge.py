"""知识检索相关 Schema（流程三）。"""
from pydantic import BaseModel


class RelatedPlanResult(BaseModel):
    document_id: str
    document_title: str
    section: str | None = None
    similarity: float
    summary: str
    citation_locator: str | None = None


class SimilarCaseResult(BaseModel):
    document_id: str
    case_name: str
    event_type: str | None = None
    main_measures: str | None = None
    outcome: str | None = None
    lessons: str | None = None


class RoleResponsibilityResult(BaseModel):
    role_name: str
    standard_responsibility: str
    handling_requirement: str | None = None
    reporting_requirement: str | None = None


class SceneKnowledgeResult(BaseModel):
    related_area: str
    channels_and_facilities: str | None = None
    scene_constraints: str | None = None
    alternative_areas: str | None = None


class RetrievalResult(BaseModel):
    """检索结果分类（第三节·3）。"""

    related_plans: list[RelatedPlanResult] = []
    similar_cases: list[SimilarCaseResult] = []
    role_responsibilities: list[RoleResponsibilityResult] = []
    scene_knowledge: list[SceneKnowledgeResult] = []


class RetrievalSelection(BaseModel):
    """人工选择结果（第三节·4）：选中/取消/标记不适用。"""

    selected_chunk_ids: list[str] = []
    excluded_chunk_ids: list[str] = []
    not_applicable_chunk_ids: list[str] = []
    manual_references: list[str] = []


class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str
    file_url: str | None = None
