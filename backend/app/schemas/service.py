from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TemplateBase(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    status: str
    tags: List[str]

class TemplateDetail(TemplateBase):
    schema: Optional[str] = None

class ServiceCreateRequest(BaseModel):
    template_id: str
    service_name: str = Field(..., min_length=1, max_length=63)
    config: Dict[str, Any]

class ServiceUpdate(BaseModel):
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class ServiceResponse(BaseModel):
    id: str
    name: str
    template: str
    status: str
    created_at: str
    namespace: str = "default"
    config: Dict[str, Any] = {}

class ServiceListResponse(BaseModel):
    services: List[ServiceResponse]
    total: int

class LogMessage(BaseModel):
    timestamp: str
    level: str  # info, warning, error, success
    message: str
    step: Optional[str] = None

class CreateServiceResponse(BaseModel):
    success: bool
    service_id: str
    message: str
    logs: List[LogMessage] = []
