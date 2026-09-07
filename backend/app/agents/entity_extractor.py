"""实体/关系抽取Agent（GraphRAG 轻量版）。从知识文档文本中抽取实体与关系，
供 GraphService 写入 Neo4j。类型体系围绕应急预案场景（岗位/设施/区域/措施/规范条文等）。
"""
from app.agents.base import BaseAgent
from app.schemas.graph import EntityExtractionOutput

PROMPT_VERSION = "entity_extractor.v1"

_JSON_SKELETON = """{
  "entities": [{"name": "string", "type": "岗位|设施|区域|措施|规范条文|事件类型|其他", "description": "string"}],
  "relationships": [{"source": "string", "target": "string", "type": "string(如 负责/位于/依据/引发/需要)", "description": "string"}]
}"""

_PROMPT_TEMPLATE = """你是应急预案知识图谱构建助手。请从以下文档内容中抽取关键实体与实体间关系，
用于构建应急处置知识图谱。实体类型聚焦：岗位、设施、区域、处置措施、规范条文、事件类型等。
关系类型用简短动词短语描述（如"负责"“位于”“依据”“引发”“需要”）。

必须严格按下面的 JSON 结构输出（字段名、层级、类型都不能更改）：
{json_skeleton}

要求：
- name 使用文档中出现的原词，不要翻译或改写；
- 同一实体在全文只出现一次（合并重复提及）；
- 关系的 source/target 必须是 entities 列表中出现过的 name；
- 最多抽取 30 个实体、40 条关系，优先保留最重要的。

文档内容：
{text}

只输出 JSON，不要输出其他说明文字，不要用 markdown 代码块包裹。
"""


class EntityExtractorAgent(BaseAgent[EntityExtractionOutput]):
    run_type = "entity_extraction"
    output_schema = EntityExtractionOutput

    def build_prompt(self, *, text: str) -> str:
        return _PROMPT_TEMPLATE.format(json_skeleton=_JSON_SKELETON, text=text)

    def extract(self, *, document_id: str, text: str) -> EntityExtractionOutput:
        prompt = self.build_prompt(text=text)
        return self.run(
            business_object_type="knowledge_document",
            business_object_id=document_id,
            prompt=prompt,
            prompt_version=PROMPT_VERSION,
        )
