"""
Multi-object tracking using Ultralytics' built-in tracking.

The trained VisDrone model is loaded through
ml.utils.config.MODEL_PATH.

BoT-SORT is used through Ultralytics.
"""

from dataclasses import (
    dataclass,
    asdict,
)

from typing import (
    List,
    Optional,
    Dict,
)

import json

from ultralytics import YOLO

from ml.utils import (
    config,
    video_utils,
)


# ============================================================
# TRACKED OBJECT
# ============================================================

@dataclass
class TrackedObject:

    track_id: int

    class_id: int

    class_name: str

    confidence: float

    bbox: List[float]

    frame: int

    timestamp: float

    def to_dict(self):
        return asdict(self)


# ============================================================
# TRACKER
# ============================================================

class Tracker:

    def __init__(
        self,
        model_path: str = None,
        tracker_name: str = None,
        conf: float = None,
        iou: float = None,
        device: str = None,
    ):

        self.model_path = (
            model_path
            or config.MODEL_PATH
        )

        self.tracker_name = (
            tracker_name
            or config.TRACKER_NAME
        )

        self.conf = (
            conf
            if conf is not None
            else config.CONF_THRESHOLD
        )

        self.iou = (
            iou
            if iou is not None
            else config.IOU_THRESHOLD
        )

        self.device = (
            device
            or config.DEVICE
        )

        print(
            "[SentinelAI] Loading model:",
            self.model_path,
        )

        self.model = YOLO(
            self.model_path
        )

    # ========================================================
    # TRACK VIDEO
    # ========================================================

    def track_video(
        self,
        video_path: str,
        output_video_path: Optional[str] = None,
    ):

        info = (
            video_utils.get_video_info(
                video_path
            )
        )

        writer = None

        if output_video_path:

            writer = (
                video_utils.make_video_writer(
                    output_video_path,
                    info.fps,
                    info.width,
                    info.height,
                )
            )

        # ----------------------------------------------------
        # Ultralytics tracking
        # ----------------------------------------------------

        results_gen = (
            self.model.track(
                source=video_path,
                tracker=self.tracker_name,
                conf=self.conf,
                iou=self.iou,
                device=self.device,
                persist=True,
                stream=True,
                verbose=False,
            )
        )

        # ----------------------------------------------------
        # Process each frame
        # ----------------------------------------------------

        for frame_idx, result in enumerate(
            results_gen
        ):

            timestamp = (
                frame_idx / info.fps
                if info.fps
                else 0.0
            )

            tracked_objects = []

            boxes = result.boxes

            names = result.names

            if (
                boxes is not None
                and boxes.id is not None
            ):

                ids = (
                    boxes.id
                    .int()
                    .tolist()
                )

                for i, track_id in enumerate(
                    ids
                ):

                    class_id = int(
                        boxes
                        .cls[i]
                        .item()
                    )

                    confidence = float(
                        boxes
                        .conf[i]
                        .item()
                    )

                    x1, y1, x2, y2 = [
                        float(value)
                        for value in (
                            boxes
                            .xyxy[i]
                            .tolist()
                        )
                    ]

                    class_name = names.get(
                        class_id,
                        str(class_id),
                    )

                    tracked_objects.append(
                        TrackedObject(
                            track_id=int(
                                track_id
                            ),
                            class_id=class_id,
                            class_name=class_name,
                            confidence=confidence,
                            bbox=[
                                x1,
                                y1,
                                x2,
                                y2,
                            ],
                            frame=frame_idx,
                            timestamp=round(
                                timestamp,
                                3,
                            ),
                        )
                    )

            # ------------------------------------------------
            # Write annotated frame
            # ------------------------------------------------

            if writer is not None:

                annotated = (
                    result.plot()
                )

                writer.write(
                    annotated
                )

            yield (
                frame_idx,
                timestamp,
                tracked_objects,
            )

        # ----------------------------------------------------
        # Close output video
        # ----------------------------------------------------

        if writer is not None:
            writer.release()

    # ========================================================
    # COLLECT COMPLETE TRACK LIST
    # ========================================================

    def track_video_to_list(
        self,
        video_path: str,
        output_video_path: Optional[str] = None,
    ) -> List[Dict]:

        all_records = []

        for (
            _,
            _,
            tracked_objects,
        ) in self.track_video(
            video_path,
            output_video_path,
        ):

            all_records.extend(
                [
                    object_.to_dict()
                    for object_
                    in tracked_objects
                ]
            )

        return all_records


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--video",
        required=True,
    )

    parser.add_argument(
        "--out_video",
        default=None,
    )

    parser.add_argument(
        "--out_json",
        default=None,
    )

    args = parser.parse_args()

    out_video = (
        args.out_video
        or str(
            config
            .OUTPUT_TRACKING_DIR
            / "tracked.mp4"
        )
    )

    out_json = (
        args.out_json
        or str(
            config
            .OUTPUT_TRACKING_DIR
            / "tracks.json"
        )
    )

    tracker = Tracker()

    records = (
        tracker.track_video_to_list(
            args.video,
            out_video,
        )
    )

    with open(
        video_utils.safe_path(
            out_json
        ),
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            records,
            f,
            indent=2,
        )

    print(
        f"Tracked {len(records)} "
        f"track-observations."
    )

    print(
        f"Saved: {out_video}"
    )

    print(
        f"Saved: {out_json}"
    )