"""
Authentication Models

User, Group, and Session models for the authentication system.
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import uuid


class UserGroupLink(SQLModel, table=True):
    """Many-to-many link between users and groups"""
    __tablename__ = "user_group_links"
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    group_id: str = Field(foreign_key="groups.id", primary_key=True)


class User(SQLModel, table=True):
    """Platform user"""
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str = Field(default="")
    name: str = Field(default="")
    role: str = Field(default="viewer")  # admin, developer, viewer
    status: str = Field(default="active")  # active, inactive, pending
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    groups: List["Group"] = Relationship(back_populates="users", link_model=UserGroupLink)


class Group(SQLModel, table=True):
    """User group for permissions"""
    __tablename__ = "groups"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = Field(default="")
    permissions: str = Field(default="")  # JSON array of permission strings
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List[User] = Relationship(back_populates="groups", link_model=UserGroupLink)


class Session(SQLModel, table=True):
    """Active user sessions"""
    __tablename__ = "sessions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True)  # Hashed JWT token for validation
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    # Optional metadata
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)


# Permission constants
class Permissions:
    """Available permissions in the system"""
    
    # Service management
    SERVICE_READ = "service:read"
    SERVICE_CREATE = "service:create"
    SERVICE_UPDATE = "service:update"
    SERVICE_DELETE = "service:delete"
    
    # User management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Group management
    GROUP_READ = "group:read"
    GROUP_MANAGE = "group:manage"
    
    # Admin
    ADMIN_ALL = "admin:all"


# Default role permissions
ROLE_PERMISSIONS = {
    "admin": [Permissions.ADMIN_ALL],
    "developer": [
        Permissions.SERVICE_READ,
        Permissions.SERVICE_CREATE,
        Permissions.SERVICE_UPDATE,
        Permissions.SERVICE_DELETE,
        Permissions.USER_READ,
    ],
    "viewer": [
        Permissions.SERVICE_READ,
        Permissions.USER_READ,
    ],
}
