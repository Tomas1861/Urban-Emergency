"""Agent 基础设施：统一处理调用记录（第八节·3）与生成失败重试（第四节·4）。

各具体 Agent（event_analyzer / knowledge_retriever / plan_generator /
task_generator / report_generator）应继承 BaseAgent，只需实现
`build_prompt()` 与声明 `output_schema`，LLM 实际调用逻辑委托给
app.services.llm_service（本身也是桩，留待接入真实模型）。
"""
import json
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.exceptions import AgentGenerationError
from app.models.agent_run import AgentRun
from app.services.llm_service import LLMService

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass
class AgentInvocation:
    run_type: str
    business_object_type: str
    business_object_id: str
    prompt: str
    prompt_version: str = "v1"


class BaseAgent(Generic[SchemaT]):
    run_type: str
    output_schema: type[SchemaT]

    def __init__(self, db: Session, llm_service: LLMService | None = None):
        self.db = db
        self.llm_service = llm_service or LLMService(db=db)

    def build_prompt(self, **kwargs) -> str:  # pragma: no cover - overridden by subclasses
        raise NotImplementedError

    def run(
        self,
        *,
        business_object_type: str,
        business_object_id: str,
        prompt: str,
        prompt_version: str = "v1",
        max_retries: int = 1,
    ) -> SchemaT:
        """第四节·4 生成失败处理：解析/校验失败时自动重试一次，仍失败则抛出可重试的业务异常。"""
        last_error_code = "UNKNOWN_ERROR"
        last_error_message = ""
        last_raw_output = ""

        for attempt in range(max_retries + 1):
            run_record = AgentRun(
                run_type=self.run_type,
                business_object_type=business_object_type,
                business_object_id=business_object_id,
                model_name=self.llm_service.model_name,
                prompt_version=prompt_version,
                input_json={"prompt": prompt, "attempt": attempt},
                status="pending",
            )
            self.db.add(run_record)
            self.db.flush()

            started = time.monotonic()
            try:
                raw_output = self.llm_service.complete(prompt)
            except Exception as exc:  # noqa: BLE001 - LLM 服务异常统一转换为生成失败
                run_record.status = "failed"
                run_record.error_message = str(exc)
                run_record.duration_ms = int((time.monotonic() - started) * 1000)
                # 调用记录必须独立于外层业务事务落库（第十二节·1 可追溯性），
                # 否则调用方后续异常回滚时会连带丢失这条失败记录。
                self.db.commit()
                last_error_code, last_error_message = "MODEL_CALL_FAILED", str(exc)
                continue

            run_record.raw_output = raw_output
            run_record.duration_ms = int((time.monotonic() - started) * 1000)

            parsed, error_code, error_message = self._parse_and_validate(raw_output)
            if parsed is not None:
                run_record.status = "success"
                run_record.parsed_output_json = parsed.model_dump(mode="json")
                self.db.commit()
                return parsed

            run_record.status = "failed"
            run_record.error_message = error_message
            self.db.commit()
            last_error_code, last_error_message, last_raw_output = error_code, error_message, raw_output

        raise AgentGenerationError(
            code=last_error_code,
            message=last_error_message or "预案生成失败，模型输出格式不完整",
            agent_run_id=run_record.id,
            retryable=True,
        )

    def _parse_and_validate(self, raw_output: str) -> tuple[SchemaT | None, str, str]:
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            return None, "JSON_PARSE_FAILED", f"模型输出无法解析为JSON: {exc}"

        try:
            return self.output_schema.model_validate(data), "", ""
        except ValidationError as exc:
            return None, "SCHEMA_VALIDATION_FAILED", str(exc)
