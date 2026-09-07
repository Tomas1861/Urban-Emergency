from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./yingji_mvp.db"
    secret_key: str = "change-me"
    storage_dir: str = "./storage"

    # 大模型服务：支持 deepseek / kimi 两个 OpenAI 兼容 provider，用 llm_provider 切换。
    llm_provider: str = "deepseek"

    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    kimi_api_key: str = ""
    kimi_api_base: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "kimi-k3"

    # GraphRAG：与 backend 同机的 Neo4j 实例，用独立的库/用户与其他项目隔离。
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # 第十二节·性能目标（开发目标，非绝对保证）
    plan_generation_timeout_seconds: int = 60
    task_generation_timeout_seconds: int = 30
    report_generation_timeout_seconds: int = 60
    knowledge_retrieval_timeout_seconds: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
