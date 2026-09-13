"""
Restricted-zone event detector.

Creates an event when a tracked person/pedestrian moves
from outside the user-defined polygon to inside it.
"""

from typing import (
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

from ml.utils.geometry import (
    bbox_bottom_center,
    point_in_polygon,
)


class RestrictedZoneDetector:

    DEFAULT_TARGET_CLASSES = {
        "person",
        "pedestrian",
        "people",
    }

    def __init__(
        self,
        polygon: Optional[
            Sequence[Tuple[float, float]]
        ] = None,
        target_classes:
        Optional[Sequence[str]] = None,
        enabled: bool = False,
    ):
        self.enabled = bool(
            enabled
        )

        self.polygon = (
            list(polygon)
            if polygon is not None
            else []
        )

        if target_classes is None:
            target_classes = (
                self.DEFAULT_TARGET_CLASSES
            )

        self.target_classes = {
            str(name).lower()
            for name in target_classes
        }

        # track_id -> previous inside/outside state
        self._state: Dict[int, bool] = {}

    def reset(self):
        self._state = {}

    def process(
        self,
        tracked_objects: List[dict],
    ) -> List[dict]:

        events = []

        # ----------------------------------------------------
        # Disabled
        # ----------------------------------------------------

        if not self.enabled:
            return events

        # ----------------------------------------------------
        # Invalid polygon
        # ----------------------------------------------------

        if len(self.polygon) < 3:
            return events

        # ----------------------------------------------------
        # Process objects
        # ----------------------------------------------------

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

            # Use the bottom-center of the
            # bounding box because this approximates
            # where the person's feet touch the ground.
            point = bbox_bottom_center(
                tuple(bbox)
            )

            is_inside = point_in_polygon(
                point,
                self.polygon,
            )

            was_inside = self._state.get(
                int(track_id),
                False,
            )

            # ------------------------------------------------
            # Outside -> inside = entry
            # ------------------------------------------------

            if (
                is_inside
                and not was_inside
            ):
                events.append(
                    {
                        "event_type":
                            "restricted_zone_entry",

                        "track_id":
                            int(track_id),

                        "timestamp":
                            float(
                                obj.get(
                                    "timestamp",
                                    0.0,
                                )
                            ),

                        "frame":
                            int(
                                obj.get(
                                    "frame",
                                    0,
                                )
                            ),

                        "severity":
                            "critical",

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
                                f"entered "
                                f"restricted zone"
                            ),
                    }
                )

            self._state[
                int(track_id)
            ] = is_inside

        return events