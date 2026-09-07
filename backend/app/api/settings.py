""""其他设置"：目前覆盖大模型 provider 切换。API Key 只回显掩码，不回显明文。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.core.response import ApiResponse, ok
from app.services.settings_service import LLM_PROVIDER_KEY, get_setting, set_setting

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mask(key: str) -> str:
    if not key:
        return ""
    return key[:6] + "…" + key[-4:] if len(key) > 12 else "…"


@router.get("/llm", response_model=ApiResponse)
def get_llm_settings(db: Session = Depends(get_db)):
    settings = get_settings()
    active = get_setting(db, LLM_PROVIDER_KEY) or settings.llm_provider
    return ok({
        "active_provider": active,
        "providers": [
            {
                "id": "deepseek",
                "model": settings.deepseek_model,
                "api_base": settings.deepseek_api_base,
                "api_key_masked": _mask(settings.deepseek_api_key),
                "configured": bool(settings.deepseek_api_key),
            },
            {
                "id": "kimi",
                "model": settings.kimi_model,
                "api_base": settings.kimi_api_base,
                "api_key_masked": _mask(settings.kimi_api_key),
                "configured": bool(settings.kimi_api_key),
            },
        ],
    })


@router.put("/llm", response_model=ApiResponse)
def update_llm_settings(provider: str, db: Session = Depends(get_db)):
    if provider not in ("deepseek", "kimi"):
        raise BusinessError("INVALID_PROVIDER", "provider 必须是 deepseek 或 kimi")
    set_setting(db, LLM_PROVIDER_KEY, provider)
    return ok({"active_provider": provider})
