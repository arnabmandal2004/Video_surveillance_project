"""
SentinelAI Live Webcam Detector

Uses the pretrained COCO YOLO11n model located at:

    E:/Video_surveillance/SentinelAI/yolo11n.pt

This module is intentionally separate from the VisDrone tracking
pipeline used by recorded-video analysis.
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

COCO_MODEL_PATH = PROJECT_ROOT / "yolo11n.pt"


# ============================================================
# DETECTOR
# ============================================================


class WebcamDetector:
    """
    Runs YOLO11n COCO inference on individual webcam frames.
    """

    def __init__(
        self,
        model_path: str | None = None,
        confidence: float = 0.25,
        device: str = "cpu",
        image_size: int = 640,
    ) -> None:  

        self.model_path = Path(
            model_path or str(COCO_MODEL_PATH)
        )

        self.confidence = confidence
        self.device = device
        self.image_size = image_size

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"COCO YOLO model not found: {self.model_path}"
            )

        print(
            f"[SentinelAI Live] Loading model: "
            f"{self.model_path}"
        )

        self.model = YOLO(str(self.model_path))

        # Prevent simultaneous YOLO calls from overlapping.
        self._lock = Lock()

    # ========================================================
    # IMAGE DECODE
    # ========================================================

    @staticmethod
    def decode_image(
        image_bytes: bytes,
    ) -> np.ndarray:

        array = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )

        frame = cv2.imdecode(
            array,
            cv2.IMREAD_COLOR,
        )

        if frame is None:
            raise ValueError(
                "Unable to decode uploaded image."
            )

        return frame

    # ========================================================
    # DETECT
    # ========================================================

    def detect_bytes(
        self,
        image_bytes: bytes,
    ) -> dict[str, Any]:

        frame = self.decode_image(image_bytes)

        return self.detect_frame(frame)

    def detect_frame(
        self,
        frame: np.ndarray,
    ) -> dict[str, Any]:

        if frame is None or frame.size == 0:
            raise ValueError(
                "Invalid image frame."
            )

        height, width = frame.shape[:2]

        with self._lock:
            results = self.model.predict(
                source=frame,
                conf=self.confidence,
                imgsz=self.image_size,
                device=self.device,
                verbose=False,
            )

        detections: list[dict[str, Any]] = []

        if not results:
            return {
                "width": width,
                "height": height,
                "detections": detections,
            }

        result = results[0]

        boxes = result.boxes

        if boxes is None:
            return {
                "width": width,
                "height": height,
                "detections": detections,
            }

        names = result.names

        for i in range(len(boxes)):

            cls_id = int(
                boxes.cls[i].item()
            )

            confidence = float(
                boxes.conf[i].item()
            )

            x1, y1, x2, y2 = [
                float(value)
                for value in boxes.xyxy[i].tolist()
            ]

            class_name = str(
                names.get(
                    cls_id,
                    cls_id,
                )
            ).strip().lower()

            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(
                        confidence,
                        4,
                    ),
                    "bbox": [
                        round(x1, 2),
                        round(y1, 2),
                        round(x2, 2),
                        round(y2, 2),
                    ],
                }
            )

        return {
            "width": width,
            "height": height,
            "detections": detections,
        }


# ============================================================
# SINGLETON
# ============================================================

_detector: WebcamDetector | None = None


def get_webcam_detector() -> WebcamDetector:

    global _detector

    if _detector is None:
        _detector = WebcamDetector()

    return _detector