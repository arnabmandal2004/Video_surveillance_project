"""
SentinelAI live webcam detection and threat alert service.

YOLO11n COCO performs object detection.
SentinelAI then applies the application-level threat policy.

When a threat is detected, the original webcam frame can be
saved automatically as a threat snapshot.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from app.config import GENERATED_DIR

from ml.detection.webcam_detector import (
    get_webcam_detector,
)


# ============================================================
# THREAT POLICY
# ============================================================

THREAT_LEVELS: dict[str, str] = {
    "knife": "HIGH",
    "scissors": "HIGH",
}


SAFE_LABEL = "SAFE"


# ============================================================
# THREAT SNAPSHOT SETTINGS
# ============================================================

THREAT_SNAPSHOT_DIR = (
    GENERATED_DIR / "threats"
)

THREAT_SNAPSHOT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# Minimum time between automatically saved
# snapshots for the same live detection stream.
THREAT_SNAPSHOT_COOLDOWN = 3.0


_last_snapshot_time = 0.0

_snapshot_lock = Lock()


# ============================================================
# THREAT CLASSIFICATION
# ============================================================

def classify_threat(
    class_name: str,
) -> tuple[bool, str, str]:

    normalized = (
        str(class_name)
        .strip()
        .lower()
    )

    severity = THREAT_LEVELS.get(
        normalized
    )

    if severity:

        return (
            True,
            severity,
            "Potential threat object detected.",
        )

    return (
        False,
        SAFE_LABEL,
        "No configured threat rule for this object.",
    )


# ============================================================
# SAVE THREAT SNAPSHOT
# ============================================================

def save_threat_snapshot(
    image_bytes: bytes,
    detections: list[dict[str, Any]],
) -> dict[str, str] | None:

    global _last_snapshot_time

    threat_detections = [
        detection
        for detection in detections
        if detection.get("is_threat")
    ]

    if not threat_detections:
        return None

    now = time.time()

    with _snapshot_lock:

        if (
            now - _last_snapshot_time
            < THREAT_SNAPSHOT_COOLDOWN
        ):
            return None

        _last_snapshot_time = now

    # --------------------------------------------------------
    # Find highest severity threat
    # --------------------------------------------------------

    severity_rank = {
        "NONE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }

    threat = max(
        threat_detections,
        key=lambda item:
            severity_rank.get(
                item.get(
                    "threat_level",
                    "NONE",
                ),
                0,
            )
    )

    object_name = (
        str(
            threat.get(
                "class_name",
                "unknown",
            )
        )
        .strip()
        .lower()
        .replace(
            " ",
            "_",
        )
    )

    confidence = float(
        threat.get(
            "confidence",
            0.0,
        )
    )

    timestamp = datetime.now()

    filename = (
        f"threat_"
        f"{timestamp:%Y%m%d_%H%M%S_%f}_"
        f"{object_name}_"
        f"{int(confidence * 100)}.jpg"
    )

    output_path = (
        THREAT_SNAPSHOT_DIR /
        filename
    )

    output_path.write_bytes(
        image_bytes
    )

    return {
        "filename": filename,
        "object": object_name,
        "threat_level": str(
            threat.get(
                "threat_level",
                "HIGH",
            )
        ),
        "confidence": str(
            round(
                confidence,
                4,
            )
        ),
        "snapshot_url": (
            f"/generated/threats/"
            f"{filename}"
        ),
        "created_at": (
            timestamp.isoformat()
        ),
    }


# ============================================================
# ANALYZE LIVE FRAME
# ============================================================

def analyze_live_frame(
    image_bytes: bytes,
) -> dict[str, Any]:

    detector = get_webcam_detector()

    result = detector.detect_bytes(
        image_bytes
    )

    final_detections: list[
        dict[str, Any]
    ] = []

    severity_rank = {
        "NONE": 0,
        "SAFE": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }

    highest_threat = "SAFE"

    threat_count = 0

    # --------------------------------------------------------
    # Process detections
    # --------------------------------------------------------

    for detection in result[
        "detections"
    ]:

        class_name = (
            detection[
                "class_name"
            ]
        )

        (
            is_threat,
            severity,
            message,
        ) = classify_threat(
            class_name
        )

        if is_threat:

            threat_count += 1

        current_rank = (
            severity_rank.get(
                severity,
                0,
            )
        )

        highest_rank = (
            severity_rank.get(
                highest_threat,
                0,
            )
        )

        if current_rank > highest_rank:

            highest_threat = severity

        final_detections.append(
            {
                **detection,
                "is_threat":
                    is_threat,
                "threat_level":
                    severity,
                "message":
                    message,
                "display_name":
                    class_name.title(),
            }
        )

    # --------------------------------------------------------
    # Save threat screenshot
    # --------------------------------------------------------

    snapshot = save_threat_snapshot(
        image_bytes,
        final_detections,
    )

    # --------------------------------------------------------
    # Build alert
    # --------------------------------------------------------

    threat_alert = None

    if snapshot is not None:

        threat_alert = {
            "triggered": True,
            "object":
                snapshot["object"],
            "threat_level":
                snapshot[
                    "threat_level"
                ],
            "confidence":
                float(
                    snapshot[
                        "confidence"
                    ]
                ),
            "snapshot_url":
                snapshot[
                    "snapshot_url"
                ],
            "filename":
                snapshot[
                    "filename"
                ],
            "created_at":
                snapshot[
                    "created_at"
                ],
            "message":
                (
                    "Potential threat detected. "
                    "Threat snapshot saved."
                ),
        }

    return {
        "width":
            result["width"],

        "height":
            result["height"],

        "detections":
            final_detections,

        "threat_count":
            threat_count,

        "highest_threat":
            highest_threat,

        "threat_alert":
            threat_alert,
    }