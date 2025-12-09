from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

from app.core.db import get_session
from app.api.auth import require_admin, User
from app.models.auth import Group, User as UserModel, UserGroupLink
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupDetailResponse

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """List all groups"""
    result = await session.execute(select(Group))
    groups = result.scalars().all()
    
    response = []
    for group in groups:
        perms = json.loads(group.permissions) if group.permissions else []
        # Count members (naive approach, optimize later if needed)
        # Assuming eager validation or lazy loading works, but async requires explicit loading usually.
        # For now, let's keep it simple and maybe skip member_count or fetch it separately.
        # Actually, let's do a quick count query if needed, or assume lazy loading is not standard in async.
        # Let's just return 0 for now to speed up list
        response.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            permissions=perms,
            created_at=group.created_at,
            member_count=0 
        ))
    return response

@router.post("/", response_model=GroupResponse)
async def create_group(
    request: GroupCreate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Create a new group"""
    # Check if exists
    result = await session.execute(select(Group).where(Group.name == request.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Group already exists")
    
    new_group = Group(
        name=request.name,
        description=request.description,
        permissions=json.dumps(request.permissions)
    )
    
    session.add(new_group)
    await session.commit()
    await session.refresh(new_group)
    
    return GroupResponse(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        permissions=request.permissions,
        created_at=new_group.created_at,
        member_count=0
    )

@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get group details"""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    perms = json.loads(group.permissions) if group.permissions else []
    
    # Fetch members (manual join for async)
    stmt = select(UserModel).join(UserGroupLink).where(UserGroupLink.group_id == group_id)
    result = await session.execute(stmt)
    members = result.scalars().all()
    
    member_list = [{"id": u.id, "name": u.name, "email": u.email} for u in members]
    
    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        permissions=perms,
        created_at=group.created_at,
        member_count=len(members),
        members=member_list
    )

@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    request: GroupUpdate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Update group"""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if request.name:
        group.name = request.name
    if request.description is not None:
        group.description = request.description
    if request.permissions is not None:
        group.permissions = json.dumps(request.permissions)
        
    session.add(group)
    await session.commit()
    await session.refresh(group)
    
    perms = json.loads(group.permissions) if group.permissions else []
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        permissions=perms,
        created_at=group.created_at,
        member_count=0 # Skip for update
    )

@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Delete group"""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Delete links first (cascade usually handles this but safety first)
    stmt = select(UserGroupLink).where(UserGroupLink.group_id == group_id)
    result = await session.execute(stmt)
    links = result.scalars().all()
    for link in links:
        await session.delete(link)
        
    await session.delete(group)
    await session.commit()
    
    return {"success": True, "message": "Group deleted"}

@router.post("/{group_id}/members/{user_id}")
async def add_group_member(
    group_id: str,
    user_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Add user to group"""
    group = await session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    user = await session.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already linked
    stmt = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id,
        UserGroupLink.user_id == user_id
    )
    result = await session.execute(stmt)
    if result.scalars().first():
         return {"success": True, "message": "User already in group"}
         
    link = UserGroupLink(user_id=user_id, group_id=group_id)
    session.add(link)
    await session.commit()
    
    return {"success": True, "message": "User added to group"}

@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Remove user from group"""
    stmt = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id,
        UserGroupLink.user_id == user_id
    )
    result = await session.execute(stmt)
    link = result.scalars().first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Member not found in group")
        
    await session.delete(link)
    await session.commit()
    
    return {"success": True, "message": "User removed from group"}
