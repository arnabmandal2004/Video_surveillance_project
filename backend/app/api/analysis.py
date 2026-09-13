from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app import (
    models,
    schemas,
)

from app.services.analysis_service import (
    run_analysis,
)


router = APIRouter(
    prefix="/api/videos",
    tags=["analysis"],
)


@router.post(
    "/{video_id}/analyze",
    response_model=schemas.AnalysisStatus,
)
def analyze_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    video = (
        db.query(
            models.Video
        )
        .filter(
            models.Video.id
            == video_id
        )
        .first()
    )

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    if (
        video.status
        == "processing"
    ):

        return schemas.AnalysisStatus(
            video_id=video_id,
            status="processing",
            message="Already in progress",
        )

    background_tasks.add_task(
        run_analysis,
        video_id,
        video.filepath,
    )

    return schemas.AnalysisStatus(
        video_id=video_id,
        status="processing",
        message="Analysis started",
    )