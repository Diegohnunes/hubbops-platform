"""
Authentication API Endpoints

Login, logout, user management, and protected route utilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.core.db import get_session
from app.core.config import settings
from app.services.auth import AuthService, get_auth_service
from app.models.auth import User, Permissions, ROLE_PERMISSIONS

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# Request/Response Models
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "viewer"
    group_ids: Optional[List[str]] = []


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None
    group_ids: List[str] = [] # Include group IDs in response


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    group_ids: Optional[List[str]] = None


class ChangePasswordRequest(BaseModel):
    new_password: str


class MessageResponse(BaseModel):
    success: bool
    message: str


# Helper to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Get the current authenticated user from the JWT token"""
    if not credentials:
        return None
    
    auth_service = AuthService(session)
    user = await auth_service.validate_token(credentials.credentials)
    return user


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication - raises 401 if not authenticated"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: User = Depends(require_auth)
) -> User:
    """Require admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def require_role(allowed_roles: List[str]):
    """Dependency factory for role-based access control"""
    async def dependency(user: User = Depends(require_auth)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of: {', '.join(allowed_roles)}"
            )
        return user
    return dependency


async def require_admin(
    user: User = Depends(require_auth)
) -> User:
    """Require admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Endpoints
@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """Authenticate user and return JWT token"""
    auth_service = AuthService(session)
    user, result = await auth_service.authenticate(request.email, request.password)
    
    if not user:
        return LoginResponse(success=False, message=result)
    
    return LoginResponse(
        success=True,
        token=result,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
):
    """Logout and invalidate the current session"""
    if not credentials:
        return MessageResponse(success=True, message="Already logged out")
    
    auth_service = AuthService(session)
    await auth_service.logout(credentials.credentials)
    
    return MessageResponse(success=True, message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(require_auth)):
    """Get current user information"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    current_user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user.
    - If auth is disabled: anyone can register
    - If auth is enabled and no users exist: first user becomes admin
    - Otherwise: only admins can register new users
    """
    auth_service = AuthService(session)
    
    # Check if this is the first user
    users = await auth_service.list_users()
    is_first_user = len(users) == 0
    
    if not is_first_user and settings.AUTH_ENABLED:
        # Require admin for new registrations
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can register new users"
            )
    
    # First user is always admin
    role = "admin" if is_first_user else request.role
    
    user, error = await auth_service.create_user(
        email=request.email,
        password=request.password,
        name=request.name,
        role=role
    )
    
    if error:
        return LoginResponse(success=False, message=error)
    
    # Auto-login after registration
    _, token = await auth_service.authenticate(request.email, request.password)
    
    return LoginResponse(
        success=True,
        token=token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        message="Registration successful" + (" (admin)" if is_first_user else "")
    )


# User management (admin only)
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """List all users (admin only)"""
    auth_service = AuthService(session)
    users = await auth_service.list_users()
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            status=u.status,
            created_at=u.created_at,
            last_login=u.last_login
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get user by ID (admin only)"""
    auth_service = AuthService(session)
    user = await auth_service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Update user (admin only)"""
    auth_service = AuthService(session)
    
    update_data = request.model_dump(exclude_none=True)
    user = await auth_service.update_user(user_id, **update_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Delete user (admin only)"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    auth_service = AuthService(session)
    success = await auth_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return MessageResponse(success=True, message="User deleted")


@router.post("/users/{user_id}/password", response_model=MessageResponse)
async def change_user_password(
    user_id: str,
    request: ChangePasswordRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Change user password (admin only)"""
    auth_service = AuthService(session)
    success = await auth_service.change_password(user_id, request.new_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return MessageResponse(success=True, message="Password changed")


@router.get("/status")
async def auth_status(
    current_user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get authentication status"""
    auth_service = AuthService(session)
    users = await auth_service.list_users()
    
    return {
        "auth_enabled": settings.AUTH_ENABLED,
        "authenticated": current_user is not None,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role
        } if current_user else None,
        "has_users": len(users) > 0,
        "first_time_setup": len(users) == 0
    }
