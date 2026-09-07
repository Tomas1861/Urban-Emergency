"""业务异常类型，统一由 main.py 中的异常处理器转换为 ApiResponse。"""


class BusinessError(Exception):
    def __init__(self, code: str, message: str, data: dict | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.data = data or {}
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(BusinessError):
    def __init__(self, message: str = "资源不存在", data: dict | None = None):
        super().__init__(code="NOT_FOUND", message=message, data=data, status_code=404)


class AgentGenerationError(BusinessError):
    """对应第四/五/六/七节生成失败处理：可携带 agent_run_id 与 retryable。"""

    def __init__(self, code: str, message: str, agent_run_id: str | None = None, retryable: bool = True):
        super().__init__(
            code=code,
            message=message,
            data={"agent_run_id": agent_run_id, "retryable": retryable},
            status_code=422,
        )


class ValidationFailedError(BusinessError):
    """对应第五节任务基础校验：存在严重问题时不允许确认。"""

    def __init__(self, message: str, violations: list[str]):
        super().__init__(code="VALIDATION_FAILED", message=message, data={"violations": violations}, status_code=422)
