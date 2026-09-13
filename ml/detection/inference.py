"""
Video-level inference: streams frames, runs detection, optionally writes an
annotated video. Keeps memory bounded by processing one frame at a time.
"""
import json
import cv2
from typing import Optional, List, Dict

from ml.detection.detector import Detector
from ml.utils import video_utils, config


COLOR = (0, 220, 0)


def draw_detections(frame, detections):
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR, 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(frame, label, (x1, max(0, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR, 1, cv2.LINE_AA)
    return frame


def run_detection_on_video(
    video_path: str,
    output_video_path: Optional[str] = None,
    output_json_path: Optional[str] = None,
    detector: Optional[Detector] = None,
) -> List[Dict]:
    """
    Streams the video, runs detection per frame, optionally saves annotated
    video + JSON of per-frame detections. Returns the list of per-frame records.
    """
    detector = detector or Detector()
    info = video_utils.get_video_info(video_path)

    writer = None
    if output_video_path:
        writer = video_utils.make_video_writer(output_video_path, info.fps, info.width, info.height)

    all_records = []
    for frame_idx, timestamp, frame in video_utils.frame_generator(video_path):
        detections = detector.detect(frame)
        record = {
            "frame": frame_idx,
            "timestamp": round(timestamp, 3),
            "detections": [d.to_dict() for d in detections],
        }
        all_records.append(record)

        if writer is not None:
            annotated = draw_detections(frame.copy(), detections)
            writer.write(annotated)

    if writer is not None:
        writer.release()

    if output_json_path:
        safe_out = video_utils.safe_path(output_json_path)
        with open(safe_out, "w") as f:
            json.dump(all_records, f, indent=2)

    return all_records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--out_video", default=None)
    parser.add_argument("--out_json", default=None)
    args = parser.parse_args()

    out_video = args.out_video or str(config.OUTPUT_DETECTION_DIR / "annotated.mp4")
    out_json = args.out_json or str(config.OUTPUT_DETECTION_DIR / "detections.json")
    records = run_detection_on_video(args.video, out_video, out_json)
    print(f"Processed {len(records)} frames. Saved: {out_video}, {out_json}")