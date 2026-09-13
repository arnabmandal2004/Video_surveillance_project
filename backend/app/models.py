from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    annotated_video_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="video", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="video", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    event_type = Column(String, nullable=False)
    track_id = Column(Integer, nullable=True)
    timestamp = Column(Float, nullable=False)
    severity = Column(String, default="warning")
    confidence = Column(Float, default=0.0)
    message = Column(String, nullable=True)

    video = relationship("Video", back_populates="events")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    type = Column(String, nullable=False)
    severity = Column(String, default="warning")
    timestamp = Column(Float, nullable=False)
    track_id = Column(Integer, nullable=True)
    status = Column(String, default="active")

    video = relationship("Video", back_populates="alerts")