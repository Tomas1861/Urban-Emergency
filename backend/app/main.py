from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401 确保所有模型在 create_all 前完成注册
from app.api import activities, executions, graph, knowledge, plans, reports, roles, scenes, settings, tasks
from app.api.events import router as events_router
from app.core.database import Base, engine
from app.core.exceptions import BusinessError
from app.core.response import fail

app = FastAPI(title="重大演绎活动应急预案智能生成系统", version="0.1.0")

# 前端为独立 Vite 开发服务器（默认 5173），本地演示环境下放开跨域。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # MVP 阶段直接建表；正式迭代请改用 alembic upgrade head（见 migrations/）。
    Base.metadata.create_all(engine)


@app.exception_handler(BusinessError)
def handle_business_error(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(exc.code, exc.message, exc.data).model_dump(mode="json"),
    )


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(activities.router)
app.include_router(roles.router)
app.include_router(scenes.router)
app.include_router(events_router)
app.include_router(knowledge.router)
app.include_router(plans.router)
app.include_router(plans.event_router)
app.include_router(tasks.router)
app.include_router(tasks.plan_router)
app.include_router(executions.router)
app.include_router(reports.router)
app.include_router(reports.event_router)
app.include_router(graph.router)
app.include_router(settings.router)
