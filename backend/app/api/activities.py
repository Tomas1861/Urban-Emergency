from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.response import ApiResponse, ok
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityOut

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("", response_model=ApiResponse)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    activity = Activity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return ok(ActivityOut.model_validate(activity).model_dump(mode="json"))


@router.get("", response_model=ApiResponse)
def list_activities(db: Session = Depends(get_db)):
    activities = db.query(Activity).order_by(Activity.created_at.desc()).all()
    return ok([ActivityOut.model_validate(a).model_dump(mode="json") for a in activities])


@router.get("/{activity_id}", response_model=ApiResponse)
def get_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise NotFoundError(f"活动不存在: {activity_id}")
    return ok(ActivityOut.model_validate(activity).model_dump(mode="json"))


@router.put("/{activity_id}", response_model=ApiResponse)
def update_activity(activity_id: str, payload: ActivityCreate, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise NotFoundError(f"活动不存在: {activity_id}")
    for field, value in payload.model_dump().items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return ok(ActivityOut.model_validate(activity).model_dump(mode="json"))
