"""
End-to-end practical evaluation: detection + tracking + events + timing/FPS.
"""
import time
from typing import Dict

from ml.detection.inference import run_detection_on_video
from ml.evaluation.detection_metrics import summarize_detection_records
from ml.events.event_engine import EventEngine
from ml.utils import video_utils


def evaluate_video(video_path: str) -> Dict:
    info = video_utils.get_video_info(video_path)

    t0 = time.time()
    detection_records = run_detection_on_video(video_path)
    detection_time = time.time() - t0
    detection_summary = summarize_detection_records(detection_records)

    t1 = time.time()
    engine = EventEngine()
    tracks, events = engine.run_on_video(video_path)
    tracking_time = time.time() - t1

    unique_track_ids = {t["track_id"] for t in tracks}
    event_type_counts = {}
    for e in events:
        event_type_counts[e["event_type"]] = event_type_counts.get(e["event_type"], 0) + 1

    total_time = detection_time + tracking_time
    approx_fps = info.frame_count / total_time if total_time > 0 else 0.0

    return {
        "video": video_path,
        "frame_count": info.frame_count,
        "duration_sec": round(info.duration_sec, 2),
        "detection": detection_summary,
        "detection_time_sec": round(detection_time, 2),
        "tracking_time_sec": round(tracking_time, 2),
        "approx_fps": round(approx_fps, 2),
        "unique_tracks": len(unique_track_ids),
        "event_counts": event_type_counts,
        "total_events": len(events),
    }


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    args = parser.parse_args()
    result = evaluate_video(args.video)
    print(json.dumps(result, indent=2))