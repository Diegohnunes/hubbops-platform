from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = ""
    permissions: List[str] = []

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class GroupResponse(GroupBase):
    id: str
    created_at: datetime
    member_count: int = 0

class GroupDetailResponse(GroupResponse):
    members: List[dict] = []  # List of minimal user info

class AddMemberRequest(BaseModel):
    user_id: str
