from ml.events.restricted_zone import RestrictedZoneDetector
from ml.events.loitering import LoiteringDetector


def make_track(track_id, bbox, frame, timestamp, class_name="person"):
    return {
        "track_id": track_id,
        "class_name": class_name,
        "bbox": bbox,
        "frame": frame,
        "timestamp": timestamp,
        "confidence": 0.9,
    }


def test_restricted_zone_fires_once_on_entry():
    polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
    detector = RestrictedZoneDetector(polygon=polygon)

    outside = make_track(1, [200, 200, 220, 220], frame=0, timestamp=0.0)
    inside = make_track(1, [40, 40, 60, 60], frame=1, timestamp=0.1)

    events_1 = detector.process([outside])
    assert events_1 == []

    events_2 = detector.process([inside])
    assert len(events_2) == 1
    assert events_2[0]["event_type"] == "restricted_zone_entry"

    # Staying inside on next frame should NOT fire again
    events_3 = detector.process([inside])
    assert events_3 == []


def test_loitering_detects_stationary_track():
    detector = LoiteringDetector(duration_threshold=5.0, distance_threshold=10.0)

    events = []
    for t in [0, 1, 2, 3, 4, 5]:
        track = make_track(7, [100, 100, 120, 120], frame=t, timestamp=float(t))
        events.extend(detector.process([track]))

    assert any(e["event_type"] == "loitering" for e in events)


def test_loitering_not_triggered_when_moving():
    detector = LoiteringDetector(duration_threshold=5.0, distance_threshold=10.0)

    events = []
    for t in range(6):
        track = make_track(7, [100 + t * 30, 100, 120 + t * 30, 120], frame=t, timestamp=float(t))
        events.extend(detector.process([track]))

    assert not any(e["event_type"] == "loitering" for e in events)