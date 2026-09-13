"""
SentinelAI backend analysis service.

Pipeline:

Uploaded Video
    ↓
VisDrone-trained YOLO11n
    ↓
BoT-SORT tracking
    ↓
Loitering event analysis
    ↓
Annotated video
    ↓
JSON report
    ↓
SQLite events / alerts
"""

import json
import sys

from collections import Counter

from pathlib import Path

from typing import List


# ============================================================
# PROJECT PATH
# ============================================================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

PROJECT_ROOT = (
    BACKEND_DIR.parent
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORTS
# ============================================================

from ml.events.event_engine import (
    EventEngine,
)

from ml.events.loitering import (
    LoiteringDetector,
)

from ml.utils import (
    config,
    video_utils,
)

from app.database import (
    SessionLocal,
)

from app import models

from app.config import (
    GENERATED_DIR,
)


# ============================================================
# HELPER — PERSON
# ============================================================

def is_person_class(
    class_name: str,
) -> bool:

    name = (
        str(class_name)
        .strip()
        .lower()
    )

    return (
        name
        in config.PERSON_CLASS_NAMES
        or
        name
        in config.COCO_PERSON_CLASS_NAMES
    )


# ============================================================
# HELPER — VEHICLE
# ============================================================

def is_vehicle_class(
    class_name: str,
) -> bool:

    name = (
        str(class_name)
        .strip()
        .lower()
    )

    return (
        name
        in config.VEHICLE_CLASS_NAMES
        or
        name
        in config.COCO_VEHICLE_CLASS_NAMES
    )


# ============================================================
# MAIN ANALYSIS
# ============================================================

def run_analysis(
    video_id: int,
    video_path: str,
):
    """
    Runs the actual ML pipeline.

    No restricted-zone UI.
    No manually drawn polygon.
    """

    db = SessionLocal()

    video = None

    try:

        # ====================================================
        # FIND VIDEO
        # ====================================================

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
            return

        video.status = "processing"

        db.commit()

        # ====================================================
        # OUTPUT PATHS
        # ====================================================

        GENERATED_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_video_path = (
            GENERATED_DIR
            / f"{video_id}_annotated.mp4"
        )

        output_events_path = (
            GENERATED_DIR
            / f"{video_id}_events.json"
        )

        output_report_path = (
            GENERATED_DIR
            / f"{video_id}_report.json"
        )

        # ====================================================
        # EVENTS
        # ====================================================

        # Restricted zone is intentionally NOT used
        # in the current UI/project MVP.
        #
        # Loitering remains available, but for a
        # 15-second video and a 30-second threshold,
        # it normally produces no events.

        detectors = [
            LoiteringDetector()
        ]

        engine = EventEngine(
            detectors=detectors
        )

        # ====================================================
        # RUN TRACKING
        # ====================================================

        tracks, events = (
            engine.run_on_video(
                video_path,
                output_video_path=str(
                    output_video_path
                ),
                output_events_json=str(
                    output_events_path
                ),
            )
        )

        # ====================================================
        # TRACK STATISTICS
        # ====================================================

        unique_track_ids = {
            int(track["track_id"])
            for track in tracks
            if track.get("track_id")
            is not None
        }

        class_to_track_ids = {}

        observation_counts = Counter()

        for track in tracks:

            class_name = str(
                track.get(
                    "class_name",
                    "unknown",
                )
            ).lower()

            track_id = track.get(
                "track_id"
            )

            observation_counts[
                class_name
            ] += 1

            if track_id is not None:

                class_to_track_ids.setdefault(
                    class_name,
                    set(),
                ).add(
                    int(track_id)
                )

        unique_objects_by_class = {
            class_name: len(track_ids)
            for (
                class_name,
                track_ids
            )
            in class_to_track_ids.items()
        }

        # ====================================================
        # EVENT COUNTS
        # ====================================================

        event_counts = Counter(
            event["event_type"]
            for event in events
        )

        # ====================================================
        # VIDEO INFORMATION
        # ====================================================

        info = (
            video_utils.get_video_info(
                video_path
            )
        )

        # ====================================================
        # PERSON COUNT
        # ====================================================

        person_track_ids = set()

        for track in tracks:

            class_name = str(
                track.get(
                    "class_name",
                    "",
                )
            )

            if is_person_class(
                class_name
            ):

                track_id = track.get(
                    "track_id"
                )

                if track_id is not None:
                    person_track_ids.add(
                        int(track_id)
                    )

        # ====================================================
        # VEHICLE COUNT
        # ====================================================

        vehicle_track_ids = set()

        for track in tracks:

            class_name = str(
                track.get(
                    "class_name",
                    "",
                )
            )

            if is_vehicle_class(
                class_name
            ):

                track_id = track.get(
                    "track_id"
                )

                if track_id is not None:
                    vehicle_track_ids.add(
                        int(track_id)
                    )

        # ====================================================
        # REPORT
        # ====================================================

        report = {
            "video_id":
                video_id,

            "filename":
                video.filename,

            "status":
                "completed",

            "video": {
                "frames":
                    int(
                        info.frame_count
                    ),

                "fps":
                    float(
                        info.fps
                    ),

                "duration_seconds":
                    float(
                        info.duration_sec
                    ),

                "width":
                    int(
                        info.width
                    ),

                "height":
                    int(
                        info.height
                    ),
            },

            "tracking": {
                "unique_tracks":
                    len(
                        unique_track_ids
                    ),

                "total_track_observations":
                    len(
                        tracks
                    ),
            },

            "objects": {
                "unique_objects_by_class":
                    unique_objects_by_class,

                "track_observations_by_class":
                    dict(
                        observation_counts
                    ),
            },

            "summary": {
                "persons":
                    len(
                        person_track_ids
                    ),

                "vehicles":
                    len(
                        vehicle_track_ids
                    ),
            },

            "events":
                dict(
                    event_counts
                ),

            "totals": {
                "unique_object_tracks":
                    len(
                        unique_track_ids
                    ),

                "track_observations":
                    len(
                        tracks
                    ),

                "events":
                    len(
                        events
                    ),
            },

            "annotated_video_url":
                (
                    f"/generated/"
                    f"{video_id}_annotated.mp4"
                ),

            "report_url":
                (
                    f"/generated/"
                    f"{video_id}_report.json"
                ),

            "events_url":
                (
                    f"/generated/"
                    f"{video_id}_events.json"
                ),
        }

        # ====================================================
        # SAVE REPORT
        # ====================================================

        with open(
            output_report_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                indent=2,
            )

        # ====================================================
        # CLEAR OLD EVENTS / ALERTS
        # ====================================================

        db.query(
            models.Event
        ).filter(
            models.Event.video_id
            == video_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            models.Alert
        ).filter(
            models.Alert.video_id
            == video_id
        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # SAVE EVENTS
        # ====================================================

        for event in events:

            event_row = models.Event(
                video_id=video_id,

                event_type=event[
                    "event_type"
                ],

                track_id=event.get(
                    "track_id"
                ),

                timestamp=float(
                    event.get(
                        "timestamp",
                        0.0,
                    )
                ),

                severity=event.get(
                    "severity",
                    "warning",
                ),

                confidence=float(
                    event.get(
                        "confidence",
                        0.0,
                    )
                ),

                message=event.get(
                    "message"
                ),
            )

            db.add(
                event_row
            )

            alert_row = models.Alert(
                video_id=video_id,

                type=event[
                    "event_type"
                ],

                severity=event.get(
                    "severity",
                    "warning",
                ),

                timestamp=float(
                    event.get(
                        "timestamp",
                        0.0,
                    )
                ),

                track_id=event.get(
                    "track_id"
                ),

                status="active",
            )

            db.add(
                alert_row
            )

        # ====================================================
        # COMPLETE
        # ====================================================

        video.status = "completed"

        video.annotated_video_path = (
            str(
                output_video_path
            )
        )

        db.commit()

        print(
            "=" * 60
        )

        print(
            "SENTINEL AI ANALYSIS COMPLETE"
        )

        print(
            "=" * 60
        )

        print(
            f"Video ID: {video_id}"
        )

        print(
            f"Model: {config.MODEL_PATH}"
        )

        print(
            f"Frames: {info.frame_count}"
        )

        print(
            f"Duration: "
            f"{info.duration_sec:.3f}s"
        )

        print(
            f"Persons: "
            f"{len(person_track_ids)}"
        )

        print(
            f"Vehicles: "
            f"{len(vehicle_track_ids)}"
        )

        print(
            f"Unique tracks: "
            f"{len(unique_track_ids)}"
        )

        print(
            f"Track observations: "
            f"{len(tracks)}"
        )

        print(
            f"Events: "
            f"{len(events)}"
        )

        print(
            "=" * 60
        )

    except Exception:

        if video is not None:

            video.status = "failed"

            db.commit()

        raise

    finally:

        db.close()