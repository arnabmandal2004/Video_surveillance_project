"""
Practical baseline metrics — not a full research benchmarking suite.
"""
from collections import Counter
from typing import List, Dict


def summarize_detection_records(records: List[Dict]) -> Dict:
    """
    records: output of inference.run_detection_on_video
    (list of {"frame", "timestamp", "detections":[...]})
    """
    class_counts = Counter()
    confidences = []
    total_detections = 0

    for record in records:
        for det in record["detections"]:
            class_counts[det["class_name"]] += 1
            confidences.append(det["confidence"])
            total_detections += 1

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "total_frames": len(records),
        "total_detections": total_detections,
        "class_counts": dict(class_counts),
        "average_confidence": round(avg_conf, 4),
    }