from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoOut(BaseModel):

    id: int

    filename: str

    status: str

    annotated_video_path: Optional[str] = None

    uploaded_at: datetime

    class Config:
        from_attributes = True


class EventOut(BaseModel):

    id: int

    event_type: str

    track_id: Optional[int] = None

    timestamp: float

    severity: str

    confidence: float

    message: Optional[str] = None

    class Config:
        from_attributes = True


class AlertOut(BaseModel):

    id: int

    type: str

    severity: str

    timestamp: float

    track_id: Optional[int] = None

    status: str

    class Config:
        from_attributes = True


class AnalysisStatus(BaseModel):

    video_id: int

    status: str

    message: Optional[str] = None