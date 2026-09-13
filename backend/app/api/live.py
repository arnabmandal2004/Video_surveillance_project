"""
API endpoints for SentinelAI Live Feeds.
"""

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.live_detection_service import (
    analyze_live_frame,
)


router = APIRouter(
    prefix="/api/live",
    tags=["live"],
)


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def live_health():

    return {
        "status": "online",
        "message":
            "SentinelAI live detection is available.",
    }


# ============================================================
# DETECT FRAME
# ============================================================

@router.post("/detect")
async def detect_live_frame(
    file: UploadFile = File(...),
):

    try:

        image_bytes = await file.read()

        if not image_bytes:

            raise HTTPException(
                status_code=400,
                detail="Empty image received.",
            )

        result = analyze_live_frame(
            image_bytes
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "[SentinelAI Live] "
            f"Detection error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Live detection failed: "
                f"{exc}"
            ),
        )