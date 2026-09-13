import os
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)


def _env_path(
    name: str,
    default: Path,
) -> Path:
    value = os.environ.get(name)

    return Path(value) if value else default


# ============================================================
# DIRECTORIES
# ============================================================

DATA_DIR = _env_path(
    "DATA_DIR",
    BASE_DIR / "data",
)

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"

SAMPLES_DIR = DATA_DIR / "samples"


OUTPUT_DIR = _env_path(
    "OUTPUT_DIR",
    BASE_DIR / "outputs",
)

OUTPUT_DETECTION_DIR = (
    OUTPUT_DIR / "detection"
)

OUTPUT_TRACKING_DIR = (
    OUTPUT_DIR / "tracking"
)

OUTPUT_EVENTS_DIR = (
    OUTPUT_DIR / "events"
)

OUTPUT_REPORTS_DIR = (
    OUTPUT_DIR / "reports"
)


MODELS_DIR = _env_path(
    "MODELS_DIR",
    BASE_DIR / "ml" / "models",
)


for directory in [
    PROCESSED_DIR,
    SAMPLES_DIR,
    OUTPUT_DETECTION_DIR,
    OUTPUT_TRACKING_DIR,
    OUTPUT_EVENTS_DIR,
    OUTPUT_REPORTS_DIR,
    MODELS_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# MODEL
# ============================================================

# IMPORTANT:
# Prefer the trained VisDrone model.
#
# Previous working training output:
# ml/models/training_runs/
#     visdrone_yolo11n/
#         weights/
#             best.pt

TRAINED_VISDRONE_MODEL = (
    BASE_DIR
    / "ml"
    / "models"
    / "training_runs"
    / "visdrone_yolo11n"
    / "weights"
    / "best.pt"
)


# Environment variable still has priority.
#
# Example:
# $env:MODEL_PATH="..."
#
# Otherwise automatically use the trained VisDrone model
# when it exists.
if os.environ.get("MODEL_PATH"):
    MODEL_PATH = os.environ["MODEL_PATH"]

elif TRAINED_VISDRONE_MODEL.exists():
    MODEL_PATH = str(
        TRAINED_VISDRONE_MODEL
    )

else:
    MODEL_PATH = "yolo11n.pt"


# ============================================================
# DETECTION
# ============================================================

CONF_THRESHOLD = float(
    os.environ.get(
        "CONF_THRESHOLD",
        0.35,
    )
)

IOU_THRESHOLD = float(
    os.environ.get(
        "IOU_THRESHOLD",
        0.45,
    )
)

DEVICE = os.environ.get(
    "DEVICE",
    "cpu",
)


# ============================================================
# VISDRONE / OBJECT CLASSES
# ============================================================

# The trained VisDrone model uses classes such as:
#
# pedestrian
# people
# bicycle
# car
# van
# truck
# tricycle
# awning-tricycle
# bus
# motor

PERSON_CLASS_NAMES = {
    "pedestrian",
    "people",
}

VEHICLE_CLASS_NAMES = {
    "bicycle",
    "car",
    "van",
    "truck",
    "tricycle",
    "awning-tricycle",
    "bus",
    "motor",
}


# Also tolerate COCO output if someone explicitly points
# MODEL_PATH at yolo11n.pt.
COCO_PERSON_CLASS_NAMES = {
    "person",
}

COCO_VEHICLE_CLASS_NAMES = {
    "car",
    "truck",
    "bus",
    "motorcycle",
    "bicycle",
}


# ============================================================
# TRACKING
# ============================================================

TRACKER_NAME = os.environ.get(
    "TRACKER_NAME",
    "botsort.yaml",
)


# ============================================================
# EVENTS
# ============================================================

LOITERING_SECONDS = float(
    os.environ.get(
        "LOITERING_SECONDS",
        30.0,
    )
)

LOITERING_DISTANCE = float(
    os.environ.get(
        "LOITERING_DISTANCE",
        40.0,
    )
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    (
        "sqlite:///"
        + str(
            (
                BASE_DIR
                / "backend"
                / "sentinel.db"
            ).as_posix()
        )
    ),
)


# ============================================================
# BACKEND DIRECTORIES
# ============================================================

UPLOAD_DIR = _env_path(
    "UPLOAD_DIR",
    BASE_DIR / "backend" / "uploads",
)

GENERATED_DIR = _env_path(
    "GENERATED_DIR",
    BASE_DIR / "backend" / "generated",
)


UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)