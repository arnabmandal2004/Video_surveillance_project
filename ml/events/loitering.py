"""
Rule-based loitering detector.

A tracked person/pedestrian is considered loitering when
they stay within a small movement range for the configured
duration.
"""

from collections import defaultdict
from typing import (
    Dict,
    List,
)

from ml.utils.geometry import (
    bbox_bottom_center,
    max_displacement,
)

from ml.utils import config


class LoiteringDetector:

    DEFAULT_TARGET_CLASSES = {
        "person",
        "pedestrian",
        "people",
    }

    def __init__(
        self,
        duration_threshold: float = None,
        distance_threshold: float = None,
        target_classes=None,
    ):

        self.duration_threshold = (
            duration_threshold
            if duration_threshold is not None
            else config.LOITERING_SECONDS
        )

        self.distance_threshold = (
            distance_threshold
            if distance_threshold is not None
            else config.LOITERING_DISTANCE
        )

        if target_classes is None:
            target_classes = (
                self.DEFAULT_TARGET_CLASSES
            )

        self.target_classes = {
            str(name).lower()
            for name in target_classes
        }

        self._history: Dict[
            int,
            List[tuple]
        ] = defaultdict(list)

        self._alerted = set()

    def reset(self):
        self._history.clear()
        self._alerted.clear()

    def process(
        self,
        tracked_objects: List[dict],
    ) -> List[dict]:

        events = []

        for obj in tracked_objects:

            class_name = str(
                obj.get(
                    "class_name",
                    "",
                )
            ).lower()

            if (
                class_name
                not in self.target_classes
            ):
                continue

            track_id = obj.get(
                "track_id"
            )

            if track_id is None:
                continue

            bbox = obj.get(
                "bbox"
            )

            if not bbox or len(bbox) != 4:
                continue

            point = bbox_bottom_center(
                tuple(bbox)
            )

            timestamp = float(
                obj.get(
                    "timestamp",
                    0.0,
                )
            )

            self._history[
                int(track_id)
            ].append(
                (
                    timestamp,
                    point,
                )
            )

            # ------------------------------------------------
            # Keep relevant time window
            # ------------------------------------------------

            history = self._history[
                int(track_id)
            ]

            cutoff = (
                timestamp
                - self.duration_threshold
            )

            history = [
                item
                for item in history
                if item[0] >= cutoff
            ]

            self._history[
                int(track_id)
            ] = history

            # ------------------------------------------------
            # Need enough time
            # ------------------------------------------------

            if not history:
                continue

            elapsed = (
                history[-1][0]
                - history[0][0]
            )

            if (
                elapsed
                < self.duration_threshold
            ):
                continue

            # ------------------------------------------------
            # Movement
            # ------------------------------------------------

            positions = [
                position
                for _, position in history
            ]

            displacement = max_displacement(
                positions
            )

            if (
                displacement
                <= self.distance_threshold
            ):

                if (
                    int(track_id)
                    not in self._alerted
                ):

                    events.append(
                        {
                            "event_type":
                                "loitering",

                            "track_id":
                                int(track_id),

                            "timestamp":
                                timestamp,

                            "frame":
                                int(
                                    obj.get(
                                        "frame",
                                        0,
                                    )
                                ),

                            "severity":
                                "warning",

                            "confidence":
                                float(
                                    obj.get(
                                        "confidence",
                                        0.0,
                                    )
                                ),

                            "message":
                                (
                                    f"Track "
                                    f"{track_id} "
                                    f"may be "
                                    f"loitering"
                                ),
                        }
                    )

                    self._alerted.add(
                        int(track_id)
                    )

        return events