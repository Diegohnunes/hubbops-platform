import pytest
from app.services.auth import AuthService
from app.models.auth import User

@pytest.mark.asyncio
async def test_create_user(session):
    """Test user creation"""
    auth_service = AuthService(session)
    
    user, error = await auth_service.create_user(
        email="test@example.com",
        password="password123",
        name="Test User",
        role="developer"
    )
    
    assert user is not None
    assert error is None
    assert user.email == "test@example.com"
    assert user.role == "developer"
    assert user.password_hash != "password123"  # Should be hashed

@pytest.mark.asyncio
async def test_authenticate_success(session):
    """Test successful authentication"""
    auth_service = AuthService(session)
    
    # Create user first
    await auth_service.create_user(
        email="login@example.com",
        password="password123",
        name="Login User"
    )
    
    user, token = await auth_service.authenticate("login@example.com", "password123")
    
    assert user is not None
    assert token is not None
    assert user.email == "login@example.com"

@pytest.mark.asyncio
async def test_authenticate_failure(session):
    """Test failed authentication"""
    auth_service = AuthService(session)
    
    user, token = await auth_service.authenticate("nonexistent@example.com", "wrongpass")
    
    assert user is None
    assert token == "Invalid email or password"

@pytest.mark.asyncio
async def test_permission_check(session):
    """Test permission checking logic"""
    auth_service = AuthService(session)
    
    admin = User(role="admin")
    dev = User(role="developer")
    viewer = User(role="viewer")
    
    # Admin has all
    assert auth_service.has_permission(admin, "any:permission") is True
    
    # Developer has service create
    assert auth_service.has_permission(dev, "service:create") is True
    # Developer does NOT have group manage
    assert auth_service.has_permission(dev, "group:manage") is False
    
    # Viewer has read
    assert auth_service.has_permission(viewer, "service:read") is True
    # Viewer does NOT have create
    assert auth_service.has_permission(viewer, "service:create") is False
