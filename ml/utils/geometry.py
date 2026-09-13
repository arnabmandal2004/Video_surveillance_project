"""
Geometry helpers reused by event detection (restricted zone, loitering).
"""
import math
from typing import List, Tuple, Sequence

BBox = Tuple[float, float, float, float]  # x1, y1, x2, y2
Point = Tuple[float, float]


def bbox_center(bbox: BBox) -> Point:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def bbox_bottom_center(bbox: BBox) -> Point:
    """Often more accurate as a 'ground position' for zone/loitering logic."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


def euclidean_distance(p1: Point, p2: Point) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def point_in_polygon(point: Point, polygon: Sequence[Point]) -> bool:
    """
    Standard ray-casting algorithm. polygon = list of (x, y) vertices, ordered.
    """
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def polygon_bounds(polygon: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (min(xs), min(ys), max(xs), max(ys))


def trajectory_distance(points: List[Point]) -> float:
    """Total path length traveled across an ordered list of points."""
    if len(points) < 2:
        return 0.0
    return sum(euclidean_distance(points[i], points[i + 1]) for i in range(len(points) - 1))


def max_displacement(points: List[Point]) -> float:
    """Max distance from the first point to any subsequent point (used for loitering)."""
    if len(points) < 2:
        return 0.0
    origin = points[0]
    return max(euclidean_distance(origin, p) for p in points[1:])