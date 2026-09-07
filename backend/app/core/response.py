"""统一接口返回规范（第十一节）。"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    code: str
    message: str
    data: Any = None
    request_id: str


def _request_id() -> str:
    return f"REQ-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"


def ok(data: Any = None, message: str = "操作成功", code: str = "OK") -> ApiResponse:
    return ApiResponse(success=True, code=code, message=message, data=data, request_id=_request_id())


def fail(code: str, message: str, data: Any = None) -> ApiResponse:
    return ApiResponse(success=False, code=code, message=message, data=data, request_id=_request_id())
