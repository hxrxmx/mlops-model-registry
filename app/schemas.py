from pydantic import BaseModel, computed_field
from typing import Optional, Dict, Any
from datetime import datetime


class ModelRegister(BaseModel):
    model_name: str
    team: str
    description: Optional[str] = None
    dvc_hash: str
    config: Dict[str, Any]
    metrics: Dict[str, Any]


class ModelVersionOut(BaseModel):
    id: int
    model_id: int
    version_number: int
    status: str
    dvc_hash: str
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    created_at: datetime

    @computed_field
    @property
    def version_name(self) -> str:
        return f"v{self.version_number}"

    class Config:
        from_attributes = True
