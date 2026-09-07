from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.response import ApiResponse, ok
from app.models.activity import Scene, SceneArea
from app.schemas.activity import SceneCreate, SceneOut

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


@router.post("", response_model=ApiResponse)
def create_scene(payload: SceneCreate, db: Session = Depends(get_db)):
    scene = Scene(
        activity_id=payload.activity_id,
        name=payload.name,
        description=payload.description,
        map_file_url=payload.map_file_url,
        metadata_json={
            "key_channels": payload.key_channels,
            "entrances": payload.entrances,
            "key_facilities": payload.key_facilities,
            "available_roles": payload.available_roles,
            "base_resources": payload.base_resources,
        },
    )
    db.add(scene)
    db.flush()
    for area in payload.areas:
        db.add(SceneArea(scene_id=scene.id, **area.model_dump()))
    db.commit()
    db.refresh(scene)
    return ok(SceneOut.model_validate(scene).model_dump(mode="json"))


@router.get("", response_model=ApiResponse)
def list_scenes(db: Session = Depends(get_db)):
    scenes = db.query(Scene).all()
    return ok([SceneOut.model_validate(s).model_dump(mode="json") for s in scenes])


@router.get("/{scene_id}", response_model=ApiResponse)
def get_scene(scene_id: str, db: Session = Depends(get_db)):
    scene = db.get(Scene, scene_id)
    if not scene:
        raise NotFoundError(f"场景不存在: {scene_id}")
    return ok(SceneOut.model_validate(scene).model_dump(mode="json"))


@router.put("/{scene_id}", response_model=ApiResponse)
def update_scene(scene_id: str, payload: SceneCreate, db: Session = Depends(get_db)):
    scene = db.get(Scene, scene_id)
    if not scene:
        raise NotFoundError(f"场景不存在: {scene_id}")
    scene.name = payload.name
    scene.description = payload.description
    scene.map_file_url = payload.map_file_url
    scene.metadata_json = {
        "key_channels": payload.key_channels,
        "entrances": payload.entrances,
        "key_facilities": payload.key_facilities,
        "available_roles": payload.available_roles,
        "base_resources": payload.base_resources,
    }
    db.commit()
    db.refresh(scene)
    return ok(SceneOut.model_validate(scene).model_dump(mode="json"))
