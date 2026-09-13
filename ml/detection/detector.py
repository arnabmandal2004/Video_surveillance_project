"""
Pure object detection wrapper around Ultralytics YOLO.
No tracking, no event logic here — single responsibility.
"""
from dataclasses import dataclass, asdict
from typing import List
import numpy as np
from ultralytics import YOLO

from ml.utils import config


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]

    def to_dict(self):
        return asdict(self)


class Detector:
    def __init__(self, model_path: str = None, conf: float = None,
                 iou: float = None, device: str = None):
        self.model_path = model_path or config.MODEL_PATH
        self.conf = conf if conf is not None else config.CONF_THRESHOLD
        self.iou = iou if iou is not None else config.IOU_THRESHOLD
        self.device = device or config.DEVICE
        self.model = YOLO(self.model_path)

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run detection on a single BGR frame. Returns structured Detection objects."""
        results = self.model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )
        detections: List[Detection] = []
        if not results:
            return detections

        result = results[0]
        names = result.names
        boxes = result.boxes
        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            detections.append(Detection(
                class_id=cls_id,
                class_name=names.get(cls_id, str(cls_id)),
                confidence=conf,
                bbox=[x1, y1, x2, y2],
            ))
        return detections