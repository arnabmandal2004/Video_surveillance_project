"""
Video I/O utilities. Streaming-friendly (no full-video load into RAM).
"""
import os
import cv2
from dataclasses import dataclass


@dataclass
class VideoInfo:
    path: str
    fps: float
    width: int
    height: int
    frame_count: int
    duration_sec: float


def open_video(path: str) -> cv2.VideoCapture:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Video not found: {path}")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise IOError(f"Failed to open video: {path}")
    return cap


def get_video_info(path: str) -> VideoInfo:
    cap = open_video(path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0.0
        return VideoInfo(path=path, fps=fps, width=width, height=height,
                          frame_count=frame_count, duration_sec=duration)
    finally:
        cap.release()


def frame_generator(path: str):
    """
    Yields (frame_idx, timestamp_sec, frame_bgr) one at a time.
    Caller is responsible for breaking out of the loop if needed.
    """
    cap = open_video(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            timestamp = idx / fps
            yield idx, timestamp, frame
            idx += 1
    finally:
        cap.release()


def make_video_writer(output_path: str, fps: float, width: int, height: int) -> cv2.VideoWriter:
    safe_output_path = safe_path(output_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(safe_output_path, fourcc, fps, (width, height))
    if not writer.isOpened():
        raise IOError(f"Failed to open video writer for: {safe_output_path}")
    return writer


def safe_path(path: str) -> str:
    """Ensure parent directory exists; return normalized (Windows-safe) path string."""
    norm = os.path.normpath(path)
    parent = os.path.dirname(norm)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return norm