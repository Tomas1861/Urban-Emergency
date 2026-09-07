"""岗位管理最小实现。第十节接口清单未给出岗位相关路径，但任务分解/事件表单等
多处前端页面需要读取岗位列表，这里补一个最小可用的 list + create，不做完整 CRUD。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse, ok
from app.models.activity import Role
from app.schemas.activity import RoleCreate, RoleOut

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=ApiResponse)
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).filter(Role.status == "active").all()
    return ok([RoleOut.model_validate(r).model_dump(mode="json") for r in roles])


@router.post("", response_model=ApiResponse)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return ok(RoleOut.model_validate(role).model_dump(mode="json"))
