"""运行时设置读写（system_settings 表），优先级高于 .env。"""
from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting

LLM_PROVIDER_KEY = "llm_provider"


def get_setting(db: Session, key: str) -> str | None:
    row = db.get(SystemSetting, key)
    return row.value if row else None


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(SystemSetting, key)
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=key, value=value))
    db.commit()
