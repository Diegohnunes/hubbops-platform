"""
Authentication Service

Handles JWT generation, password hashing, and session management.
"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.auth import User, Session, Group, ROLE_PERMISSIONS, Permissions, UserGroupLink
from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def get_secret_key() -> str:
    """Get JWT secret key from config or generate a default"""
    secret = settings.JWT_SECRET
    if not secret:
        # Generate a deterministic key for development
        # In production, this should be set via environment
        secret = "dev-secret-change-in-production-" + hashlib.sha256(b"hubbops").hexdigest()[:32]
    return secret


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.TOKEN_EXPIRY_HOURS))
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage (for session tracking)"""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """Authentication service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def authenticate(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user and return (user, token) or (None, error_message)
        """
        # Find user
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "Invalid email or password"
        
        if user.status != "active":
            return None, "Account is not active"
        
        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password"
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        
        # Create token
        token = create_access_token(user.id, user.email, user.role)
        
        # Create session record
        session_record = Session(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRY_HOURS)
        )
        self.session.add(session_record)
        await self.session.commit()
        
        return user, token
    
    async def validate_token(self, token: str) -> Optional[User]:
        """Validate a token and return the user if valid"""
        payload = decode_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Check if session exists and is not expired
        token_hash = hash_token(token)
        result = await self.session.execute(
            select(Session).where(
                Session.token_hash == token_hash,
                Session.expires_at > datetime.utcnow()
            )
        )
        session_record = result.scalar_one_or_none()
        
        if not session_record:
            return None
        
        # Get user
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def logout(self, token: str) -> bool:
        """Invalidate a session"""
        token_hash = hash_token(token)
        result = await self.session.execute(
            select(Session).where(Session.token_hash == token_hash)
        )
        session_record = result.scalar_one_or_none()
        
        if session_record:
            await self.session.delete(session_record)
            await self.session.commit()
            return True
        return False

    async def create_user(
        self, 
        email: str, 
        password: str, 
        name: str, 
        role: str = "viewer",
        group_ids: Optional[list[str]] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user"""
        # Check if email exists
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            return None, "Email already registered"
        
        # Validate role
        if role not in ROLE_PERMISSIONS:
            return None, f"Invalid role. Must be one of: {', '.join(ROLE_PERMISSIONS.keys())}"
        
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=role,
            status="active"
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        # Handle Groups
        if group_ids:
            for gid in group_ids:
                # verify group exists (optional but good practice)
                group = await self.session.get(Group, gid)
                if group:
                    link = UserGroupLink(user_id=user.id, group_id=gid)
                    self.session.add(link)
            await self.session.commit()
        
        return user, None
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def list_users(self) -> list[User]:
        """List all users"""

        result = await self.session.execute(select(User))
        return result.scalars().all()
    
    async def update_user(self, user_id: str, group_ids: Optional[list[str]] = None, **kwargs) -> Optional[User]:
        """Update a user"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ["id", "password_hash", "created_at"]:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.session.add(user)
        
        # Handle Groups update
        if group_ids is not None:
            # Clear existing links
            stmt = select(UserGroupLink).where(UserGroupLink.user_id == user_id)
            result = await self.session.execute(stmt)
            for link in result.scalars().all():
                await self.session.delete(link)
            
            # Add new links
            for gid in group_ids:
                group = await self.session.get(Group, gid)
                if group:
                    link = UserGroupLink(user_id=user.id, group_id=gid)
                    self.session.add(link)

        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True
    
    async def change_password(self, user_id: str, new_password: str) -> bool:
        """Change a user's password"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        return True
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if a user has a specific permission"""
        role_perms = ROLE_PERMISSIONS.get(user.role, [])
        
        # Admin has all permissions
        if Permissions.ADMIN_ALL in role_perms:
            return True
        
        return permission in role_perms
    
    async def ensure_admin_exists(self):
        """Ensure at least one admin user exists"""
        result = await self.session.execute(
            select(User).where(User.role == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            # Create default admin
            default_email = settings.DEFAULT_ADMIN_EMAIL
            default_password = "admin123"  # Should be changed on first login!
            
            user, error = await self.create_user(
                email=default_email,
                password=default_password,
                name="Administrator",
                role="admin"
            )
            
            if user:
                print(f"✅ Created default admin: {default_email} (password: admin123)")
                print("⚠️  IMPORTANT: Change this password immediately!")
            else:
                print(f"⚠️  Could not create default admin: {error}")


async def get_auth_service(session: AsyncSession) -> AuthService:
    """Dependency injection for auth service"""
    return AuthService(session)
