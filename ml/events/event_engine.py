"""
Coordinates all event detectors over a tracking stream.

SentinelAI MVP:
    YOLO / trained VisDrone model
        ↓
    BoT-SORT tracking
        ↓
    Event detectors
        ↓
    Events JSON

Restricted-zone UI has been removed from the frontend.
The existing RestrictedZoneDetector remains available for
tests/future use, but this default EventEngine does not require
a RESTRICTED_ZONE_ENABLED config variable.
"""

import json
from typing import List, Optional

from ml.tracking.tracker import Tracker
from ml.events.restricted_zone import RestrictedZoneDetector
from ml.events.loitering import LoiteringDetector
from ml.utils import config, video_utils


class EventEngine:

    def __init__(
        self,
        detectors: Optional[List] = None,
    ):
        """
        Create the event engine.

        By default:
            - RestrictedZoneDetector()
            - LoiteringDetector()

        RestrictedZoneDetector uses its own configured polygon,
        while the frontend does not expose zone creation.
        """

        self.detectors = detectors or [
            RestrictedZoneDetector(),
            LoiteringDetector(),
        ]

    # ========================================================
    # PROCESS ONE FRAME
    # ========================================================

    def process_frame(
        self,
        tracked_objects: List[dict],
    ) -> List[dict]:

        events = []

        for detector in self.detectors:

            events.extend(
                detector.process(
                    tracked_objects
                )
            )

        return events

    # ========================================================
    # RUN COMPLETE VIDEO
    # ========================================================

    def run_on_video(
        self,
        video_path: str,
        tracker: Optional[Tracker] = None,
        output_video_path: Optional[str] = None,
        output_events_json: Optional[str] = None,
    ):
        """
        Runs tracking + event detection.

        Returns:
            (
                all_tracks,
                all_events
            )
        """

        tracker = (
            tracker
            if tracker is not None
            else Tracker()
        )

        all_tracks = []

        all_events = []

        # ----------------------------------------------------
        # Track video frame-by-frame
        # ----------------------------------------------------

        for (
            frame_idx,
            timestamp,
            tracked_objects,
        ) in tracker.track_video(
            video_path,
            output_video_path,
        ):

            obj_dicts = [
                obj.to_dict()
                for obj in tracked_objects
            ]

            all_tracks.extend(
                obj_dicts
            )

            frame_events = (
                self.process_frame(
                    obj_dicts
                )
            )

            all_events.extend(
                frame_events
            )

        # ----------------------------------------------------
        # Save events JSON
        # ----------------------------------------------------

        if output_events_json:

            with open(
                video_utils.safe_path(
                    output_events_json
                ),
                "w",
                encoding="utf-8",
            ) as f:

                json.dump(
                    all_events,
                    f,
                    indent=2,
                )

        return (
            all_tracks,
            all_events,
        )


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run SentinelAI tracking "
            "and event detection."
        )
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to input video",
    )

    parser.add_argument(
        "--out_video",
        default=None,
        help="Output annotated video",
    )

    parser.add_argument(
        "--out_events",
        default=None,
        help="Output events JSON",
    )

    args = parser.parse_args()

    out_video = (
        args.out_video
        or str(
            config.OUTPUT_TRACKING_DIR
            / "annotated_tracked.mp4"
        )
    )

    out_events = (
        args.out_events
        or str(
            config.OUTPUT_EVENTS_DIR
            / "events.json"
        )
    )

    print(
        "=" * 60
    )

    print(
        "SENTINEL AI EVENT ENGINE"
    )

    print(
        "=" * 60
    )

    print(
        f"Video: {args.video}"
    )

    print(
        f"Model: {config.MODEL_PATH}"
    )

    print()

    engine = EventEngine()

    tracks, events = (
        engine.run_on_video(
            args.video,
            output_video_path=out_video,
            output_events_json=out_events,
        )
    )

    unique_tracks = {
        track["track_id"]
        for track in tracks
        if track.get("track_id")
        is not None
    }

    event_counts = {}

    for event in events:

        event_type = event[
            "event_type"
        ]

        event_counts[
            event_type
        ] = (
            event_counts.get(
                event_type,
                0,
            )
            + 1
        )

    print(
        f"Track observations: "
        f"{len(tracks)}"
    )

    print(
        f"Unique tracks: "
        f"{len(unique_tracks)}"
    )

    print(
        f"Events: "
        f"{len(events)}"
    )

    if event_counts:

        for (
            event_type,
            count,
        ) in event_counts.items():

            print(
                f" - {event_type}: "
                f"{count}"
            )

    else:

        print(
            " - No events detected"
        )

    print()

    print(
        f"Annotated video: "
        f"{out_video}"
    )

    print(
        f"Events JSON: "
        f"{out_events}"
    )

    print(
        "=" * 60
    )