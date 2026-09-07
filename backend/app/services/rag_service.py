"""检索增强服务（桩）：语义检索 knowledge_chunks 并按类别整理结果。

TODO: 接入真实向量库/embedding 模型。当前 search() 返回空结果，
知识检索Agent与前端可先联调数据流转，后续替换本文件内部实现即可。
"""
from sqlalchemy.orm import Session

from app.schemas.knowledge import RetrievalResult


class RagService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, query_text: str, *, top_k: int = 10) -> RetrievalResult:
        """按第三节·2 检索范围（预案/案例/场地资料/岗位职责/模板）执行语义检索，
        并按第三节·3 分类返回。TODO: 实现向量检索 + 相似度排序。
        """
        return RetrievalResult()
