"""
SentinelAI end-to-end demo.

Usage:
    python run_demo.py --video path/to/video.mp4
"""

import argparse
import csv
import time

from ml.events.event_engine import EventEngine
from ml.evaluation.detection_metrics import summarize_detection_records
from ml.detection.inference import run_detection_on_video
from ml.utils import config, video_utils


def main():
    parser = argparse.ArgumentParser(
        description="SentinelAI end-to-end demo"
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to input video"
    )

    args = parser.parse_args()
    video_path = args.video

    # --------------------------------------------------
    # Video information
    # --------------------------------------------------
    info = video_utils.get_video_info(video_path)

    print("=" * 50)
    print("SENTINEL AI DEMO")
    print("=" * 50)

    print(f"Video: {video_path}")
    print(f"Frames: {info.frame_count}")
    print(f"Duration: {round(info.duration_sec, 2)}s")
    print()

    # --------------------------------------------------
    # Detection
    # --------------------------------------------------
    print("Running object detection...")

    t0 = time.time()

    detection_records = run_detection_on_video(
        video_path
    )

    det_summary = summarize_detection_records(
        detection_records
    )

    det_time = time.time() - t0

    print("Detection completed.")
    print()

    # --------------------------------------------------
    # Tracking + Events
    # --------------------------------------------------
    print("Running tracking + event detection...")

    out_video = str(
        config.OUTPUT_TRACKING_DIR / "demo_tracked.mp4"
    )

    out_events_json = str(
        config.OUTPUT_EVENTS_DIR / "demo_events.json"
    )

    out_tracks_csv = str(
        config.OUTPUT_TRACKING_DIR / "demo_tracks.csv"
    )

    engine = EventEngine()

    t1 = time.time()

    tracks, events = engine.run_on_video(
        video_path,
        output_video_path=out_video,
        output_events_json=out_events_json
    )

    track_time = time.time() - t1

    # --------------------------------------------------
    # Unique tracks
    # --------------------------------------------------
    unique_tracks = {
        t["track_id"]
        for t in tracks
        if "track_id" in t
    }

    # --------------------------------------------------
    # Save tracking CSV
    # --------------------------------------------------
    fieldnames = [
        "frame",
        "timestamp",
        "track_id",
        "class_id",
        "class_name",
        "confidence",
        "bbox"
    ]

    with open(
        video_utils.safe_path(out_tracks_csv),
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for t in tracks:
            writer.writerow({
                "frame": t.get("frame"),
                "timestamp": t.get("timestamp"),
                "track_id": t.get("track_id"),
                "class_id": t.get("class_id"),
                "class_name": t.get("class_name"),
                "confidence": t.get("confidence"),
                "bbox": t.get("bbox")
            })

    # --------------------------------------------------
    # Event counts
    # --------------------------------------------------
    event_counts = {}

    for event in events:
        event_type = event.get(
            "event_type",
            "unknown"
        )

        event_counts[event_type] = (
            event_counts.get(event_type, 0) + 1
        )

    # --------------------------------------------------
    # Print object summary
    # --------------------------------------------------
    print()
    print("OBJECTS")

    if det_summary["class_counts"]:
        for cls, count in det_summary[
            "class_counts"
        ].items():

            print(f"  {cls}: {count}")
    else:
        print("  No objects detected")

    # --------------------------------------------------
    # Track summary
    # --------------------------------------------------
    print()
    print(f"Unique Tracks: {len(unique_tracks)}")
    print(f"Track Observations: {len(tracks)}")

    # --------------------------------------------------
    # Event summary
    # --------------------------------------------------
    print()
    print("EVENTS")

    if event_counts:
        for event_type, count in event_counts.items():
            print(
                f"  {event_type}: {count}"
            )
    else:
        print("  No events detected")

    # --------------------------------------------------
    # Timing
    # --------------------------------------------------
    print()

    print(
        f"Detection time: "
        f"{round(det_time, 2)}s"
    )

    print(
        f"Tracking + Events time: "
        f"{round(track_time, 2)}s"
    )

    # --------------------------------------------------
    # Outputs
    # --------------------------------------------------
    print()
    print("OUTPUT FILES")

    print(f"  Tracking video:")
    print(f"    {out_video}")

    print(f"  Events JSON:")
    print(f"    {out_events_json}")

    print(f"  Tracking CSV:")
    print(f"    {out_tracks_csv}")

    print()
    print("=" * 50)
    print("SENTINEL AI DEMO COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    main()