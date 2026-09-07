"""大模型调用服务：接入 DeepSeek / Kimi(Moonshot) 两个 OpenAI 兼容 provider。

通过 LLM_PROVIDER 环境变量切换（见 app/core/config.py）。BaseAgent.run() 已经处理了
JSON 解析校验、失败重试、调用记录，本文件只负责把 prompt 发出去、把原始文本收回来。
"""
import re

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMService:
    def __init__(self, db: Session | None = None):
        settings = get_settings()
        provider = self._resolve_provider(db) or settings.llm_provider

        if provider == "kimi":
            self.api_base = settings.kimi_api_base
            self.api_key = settings.kimi_api_key
            self.model_name = settings.kimi_model
        else:
            self.api_base = settings.deepseek_api_base
            self.api_key = settings.deepseek_api_key
            self.model_name = settings.deepseek_model

        self.provider = provider

    @staticmethod
    def _resolve_provider(db: Session | None) -> str | None:
        """system_settings 表里的 llm_provider 优先于 .env，供 admin 平台"设置"页动态切换。"""
        if db is None:
            return None
        from app.services.settings_service import LLM_PROVIDER_KEY, get_setting

        return get_setting(db, LLM_PROVIDER_KEY)

    def complete(self, prompt: str, *, temperature: float = 0.2) -> str:
        """调用大模型并返回原始文本（预期为 JSON 字符串）。"""
        if not self.api_key:
            raise RuntimeError(f"未配置 {self.provider} 的 API Key，请检查 .env 中的相关配置")

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            # kimi-k3 是推理模型，只接受 temperature=1（拒绝其他值）；其余 provider 用传入值。
            "temperature": 1 if self.provider == "kimi" else temperature,
            "messages": [
                {
                    "role": "system",
                    "content": "你是重大演绎活动应急预案智能生成系统的后台Agent。严格只输出符合要求的JSON文本，"
                    "不要输出markdown代码块标记，不要输出任何解释性文字。",
                },
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        with httpx.Client(timeout=90) as client:
            response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _strip_code_fence(content)


def _strip_code_fence(text: str) -> str:
    """部分模型即使被要求也仍会用 ```json ... ``` 包裹输出，这里做防御性剥离。"""
    return _CODE_FENCE_RE.sub("", text.strip()).strip()
