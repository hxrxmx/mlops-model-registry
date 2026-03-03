from sqlalchemy import \
    Column, Integer, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base

import enum


class ModelStatus(enum.Enum):
    NONE = "none"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    team = Column(String, index=True)
    description = Column(String)
    versions = relationship("ModelVersion", back_populates="parent_model")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    version_number = Column(Integer, nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.NONE)

    dvc_hash = Column(String, nullable=False)

    config = Column(JSON)
    metrics = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent_model = relationship("Model", back_populates="versions")
