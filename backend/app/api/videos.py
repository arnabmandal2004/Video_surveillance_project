import json
import shutil
from pathlib import Path

import cv2

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import (
    UPLOAD_DIR,
    GENERATED_DIR,
)


router = APIRouter(
    prefix="/api/videos",
    tags=["videos"],
)


# ============================================================
# UPLOAD VIDEO
# ============================================================

@router.post(
    "/upload",
    response_model=schemas.VideoOut,
)
def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided",
        )

    Path(UPLOAD_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(GENERATED_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        Path(UPLOAD_DIR)
        / file.filename
    )

    try:
        with open(
            destination,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save video: {exc}",
        )

    video = models.Video(
        filename=file.filename,
        filepath=str(destination),
        status="uploaded",
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    # --------------------------------------------------------
    # Extract first frame for browser preview
    # --------------------------------------------------------

    preview_path = (
        Path(GENERATED_DIR)
        / f"{video.id}_preview.jpg"
    )

    try:

        cap = cv2.VideoCapture(
            str(destination)
        )

        if not cap.isOpened():
            raise RuntimeError(
                "OpenCV could not open uploaded video."
            )

        success, frame = cap.read()

        cap.release()

        if not success or frame is None:
            raise RuntimeError(
                "Could not read first frame."
            )

        ok = cv2.imwrite(
            str(preview_path),
            frame,
        )

        if not ok:
            raise RuntimeError(
                "Could not save preview image."
            )

    except Exception as exc:

        # Video itself was uploaded successfully.
        # Preview failure should not delete the DB record.
        print(
            f"[SentinelAI] Preview generation failed "
            f"for video {video.id}: {exc}"
        )

    return video


# ============================================================
# VIDEO
# ============================================================

@router.get(
    "/{video_id}",
    response_model=schemas.VideoOut,
)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    return video


# ============================================================
# FIRST-FRAME PREVIEW
# ============================================================

@router.get(
    "/{video_id}/preview"
)
def get_video_preview(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    preview_path = (
        Path(GENERATED_DIR)
        / f"{video_id}_preview.jpg"
    )

    # Generate preview if missing.
    if not preview_path.exists():

        cap = cv2.VideoCapture(
            video.filepath
        )

        if not cap.isOpened():
            raise HTTPException(
                status_code=500,
                detail="Could not open video for preview.",
            )

        success, frame = cap.read()

        cap.release()

        if not success or frame is None:
            raise HTTPException(
                status_code=500,
                detail="Could not extract first frame.",
            )

        ok = cv2.imwrite(
            str(preview_path),
            frame,
        )

        if not ok:
            raise HTTPException(
                status_code=500,
                detail="Could not save preview frame.",
            )

    return FileResponse(
        path=str(preview_path),
        media_type="image/jpeg",
        filename=preview_path.name,
    )


# ============================================================
# EVENTS
# ============================================================

@router.get(
    "/{video_id}/events",
    response_model=list[schemas.EventOut],
)
def get_video_events(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    return (
        db.query(models.Event)
        .filter(
            models.Event.video_id
            == video_id
        )
        .order_by(
            models.Event.timestamp.asc()
        )
        .all()
    )


# ============================================================
# REPORT
# ============================================================

@router.get(
    "/{video_id}/report"
)
def get_video_report(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    report_path = (
        Path(GENERATED_DIR)
        / f"{video_id}_report.json"
    )

    if report_path.exists():

        try:

            with open(
                report_path,
                "r",
                encoding="utf-8",
            ) as f:

                report = json.load(f)

            report["video_id"] = video.id
            report["filename"] = video.filename
            report["status"] = video.status

            return report

        except (
            json.JSONDecodeError,
            OSError,
        ):
            pass

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    events = (
        db.query(models.Event)
        .filter(
            models.Event.video_id
            == video_id
        )
        .all()
    )

    frames = 0
    fps = 0.0
    duration = 0.0

    try:

        cap = cv2.VideoCapture(
            video.filepath
        )

        if cap.isOpened():

            frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            fps = float(
                cap.get(
                    cv2.CAP_PROP_FPS
                )
                or 0.0
            )

            if fps > 0:
                duration = (
                    frames / fps
                )

        cap.release()

    except Exception:
        pass

    event_counts = {}

    for event in events:

        event_counts[
            event.event_type
        ] = (
            event_counts.get(
                event.event_type,
                0,
            )
            + 1
        )

    unique_tracks = {
        event.track_id
        for event in events
        if event.track_id is not None
    }

    annotated_url = None

    if video.annotated_video_path:

        annotated_url = (
            "/generated/"
            + Path(
                video.annotated_video_path
            ).name
        )

    preview_url = (
        f"/api/videos/{video_id}/preview"
    )

    return {
        "video_id": video.id,
        "filename": video.filename,
        "status": video.status,

        "video": {
            "frames": frames,
            "fps": fps,
            "duration_seconds": duration,
        },

        "tracking": {
            "unique_tracks":
                len(unique_tracks),

            "total_track_observations":
                0,
        },

        "objects": {
            "unique_objects_by_class": {},
            "track_observations_by_class": {},
        },

        "events": event_counts,

        "restricted_zone": {
            "enabled": False,
            "points": [],
        },

        "totals": {
            "unique_object_tracks":
                len(unique_tracks),

            "track_observations": 0,
            "events": len(events),
        },

        "annotated_video_url":
            annotated_url,

        "preview_url":
            preview_url,

        "report_url":
            (
                f"/generated/"
                f"{report_path.name}"
            )
            if report_path.exists()
            else None,
    }


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{video_id}"
)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found",
        )

    if video.status == "processing":
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot delete video while "
                "analysis is processing."
            ),
        )

    # Source
    source_path = Path(
        video.filepath
    )

    try:
        if source_path.exists():
            source_path.unlink()
    except OSError:
        pass

    # Annotated
    if video.annotated_video_path:

        annotated_path = Path(
            video.annotated_video_path
        )

        try:
            if annotated_path.exists():
                annotated_path.unlink()
        except OSError:
            pass

    # Generated files
    generated_files = [
        Path(GENERATED_DIR)
        / f"{video_id}_preview.jpg",

        Path(GENERATED_DIR)
        / f"{video_id}_report.json",

        Path(GENERATED_DIR)
        / f"{video_id}_events.json",
    ]

    for path in generated_files:

        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    # Events
    db.query(
        models.Event
    ).filter(
        models.Event.video_id
        == video_id
    ).delete(
        synchronize_session=False
    )

    # Alerts
    db.query(
        models.Alert
    ).filter(
        models.Alert.video_id
        == video_id
    ).delete(
        synchronize_session=False
    )

    db.delete(video)

    db.commit()

    return {
        "message":
            "Video deleted successfully",

        "video_id":
            video_id,
    }