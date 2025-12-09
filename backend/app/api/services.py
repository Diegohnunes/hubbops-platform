from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from typing import List
import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import subprocess

from app.schemas.service import (
    ServiceCreateRequest, 
    ServiceResponse, 
    ServiceListResponse,
    CreateServiceResponse,
    LogMessage,
    ServiceUpdate
)
from app.models.service import Service
from app.core.config import settings
from app.services.process_manager import ProcessManager, manager
from app.api.auth import require_auth, require_role, User
from app.core.db import get_session

router = APIRouter(prefix="/services", tags=["services"])

@router.post("/", response_model=CreateServiceResponse)
async def create_service(
    request: ServiceCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_role(["admin", "developer"])),
    session: AsyncSession = Depends(get_session)
):
    """Create a new service"""
    # Normalize service_name to be DNS-compliant (namespace name)
    namespace = request.service_name.lower().replace('_', '-').replace(' ', '-')
    service_id = f"{namespace}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create service record
    import json
    
    # Add service_name to config for handlers
    config = request.config.copy()
    config["service_name"] = request.service_name
    
    service = Service(
        id=service_id,
        name=request.service_name,
        template=request.template_id,
        status="creating",
        namespace=namespace,
        config_json=json.dumps(config)
    )
    
    session.add(service)
    await session.commit()
    
    # Use new handler-based command with JSON config
    # This passes ALL form fields to the handler
    config_json = json.dumps(config).replace("'", "\\'")  # Escape for shell
    
    # Pass GitOps settings via environment variables
    import os
    env = {
        **os.environ.copy(),
        "HUBBOPS_GIT_INFRA_REPO": settings.GIT_INFRA_REPO,
        "HUBBOPS_GIT_APPS_REPO": settings.GIT_APPS_REPO,
    }
    
    # Check for persistent SSH key from Settings
    ssh_key_path = "/data/ssh/id_rsa"
    if os.path.exists(ssh_key_path):
        env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
    
    command = f"python3 -u ops-cli/main.py create --template {request.template_id} --config '{config_json}'"
    cwd = "/app"
    
    # Start background task
    background_tasks.add_task(ProcessManager.run_command, command, service_id, cwd, env)
    
    return CreateServiceResponse(
        success=True,
        service_id=service_id,
        message=f"Service creation initiated in namespace {namespace}",
        logs=[
            LogMessage(
                timestamp=datetime.now().isoformat(),
                level="info",
                message=f"Using template: {request.template_id}",
                step="initialization"
            ),
            LogMessage(
                timestamp=datetime.now().isoformat(),
                level="info",
                message=f"Service will be created in namespace: {namespace}",
                step="initialization"
            )
        ]
    )

@router.get("/", response_model=ServiceListResponse)
async def list_services(
    include_deleted: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """List all services"""
    query = select(Service)
    if not include_deleted:
        query = query.where(Service.deleted_at == None)
    
    # Order by created_at descending (most recent first)
    query = query.order_by(Service.created_at.desc())
        
    result = await session.execute(query)
    services = result.scalars().all()
    
    return ServiceListResponse(
        services=[
            ServiceResponse(
                id=s.id,
                name=s.name,
                template=s.template,
                status=s.status,
                created_at=s.created_at.isoformat(),
                namespace=s.namespace,
                config=s.config
            ) for s in services
        ],
        total=len(services)
    )

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str, session: AsyncSession = Depends(get_session)):
    """Get service details"""
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return ServiceResponse(
        id=service.id,
        name=service.name,
        template=service.template,
        status=service.status,
        created_at=service.created_at.isoformat(),
        namespace=service.namespace,
        config=service.config
    )

@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service_update: ServiceUpdate,
    user: User = Depends(require_role(["admin", "developer"])),
    session: AsyncSession = Depends(get_session)
):
    """Update service status (activate/deactivate) - scales deployment"""
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Update status in database
    if status:
        service.status = status
        await session.commit()
    
    # Scale deployment based on status
    # Scale deployment based on status
    try:
        if status == "inactive":
            # 1. Disable ArgoCD auto-sync to prevent reversion
            argocd_app = service.name.lower()
            # Use JSON patch format that works reliably with kubectl
            patch_json = '{"spec":{"syncPolicy":{"automated":null}}}'
            patch_cmd = f"kubectl patch application {argocd_app} -n argocd --type merge -p '{patch_json}'"
            subprocess.run(patch_cmd, shell=True, capture_output=True)
            
            # 2. Scale to 0 replicas (pause)
            # Try to scale deployment with service name first
            command = f"kubectl scale deployment {service.name} -n {service.namespace} --replicas=0"
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            # If failed, try to find any deployment in the namespace and scale it
            if result.returncode != 0:
                find_deploy_cmd = f"kubectl get deployments -n {service.namespace} -o jsonpath='{{.items[0].metadata.name}}'"
                deploy_result = subprocess.run(find_deploy_cmd, shell=True, capture_output=True, text=True)
                if deploy_result.returncode == 0 and deploy_result.stdout.strip():
                    deploy_name = deploy_result.stdout.strip()
                    command = f"kubectl scale deployment {deploy_name} -n {service.namespace} --replicas=0"
                    result = subprocess.run(command.split(), capture_output=True, text=True)
                
                # If still failed, try default namespace as fallback
                if result.returncode != 0:
                    command = f"kubectl scale deployment {service.name} -n default --replicas=0"
                    result = subprocess.run(command.split(), capture_output=True, text=True)
            
        elif status == "active":
            # 1. Scale to 1 replica (resume)
            command = f"kubectl scale deployment {service.name} -n {service.namespace} --replicas=1"
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            # If failed, try to find any deployment in the namespace
            if result.returncode != 0:
                find_deploy_cmd = f"kubectl get deployments -n {service.namespace} -o jsonpath='{{.items[0].metadata.name}}'"
                deploy_result = subprocess.run(find_deploy_cmd, shell=True, capture_output=True, text=True)
                if deploy_result.returncode == 0 and deploy_result.stdout.strip():
                    deploy_name = deploy_result.stdout.strip()
                    command = f"kubectl scale deployment {deploy_name} -n {service.namespace} --replicas=1"
                    result = subprocess.run(command.split(), capture_output=True, text=True)
                
                # If still failed, try default namespace as fallback
                if result.returncode != 0:
                    command = f"kubectl scale deployment {service.name} -n default --replicas=1"
                    result = subprocess.run(command.split(), capture_output=True, text=True)
            
            # 2. Re-enable ArgoCD auto-sync
            argocd_app = service.name.lower()
            patch_json = '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
            patch_cmd = f"kubectl patch application {argocd_app} -n argocd --type merge -p '{patch_json}'"
            subprocess.run(patch_cmd, shell=True, capture_output=True)
            
        else:
            return {"message": "Status updated", "status": status}
        
        if result.returncode != 0:
            raise Exception(f"Failed to scale deployment: {result.stderr}")
            
        return {
            "message": f"Service {'paused' if status == 'inactive' else 'resumed'}",
            "status": status
        }
    except Exception as e:
        # Log error but don't fail the request completely if possible, or return 500
        print(f"Error scaling service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    user: User = Depends(require_role(["admin"])),
    session: AsyncSession = Depends(get_session)
):
    """Soft delete service: Mark as deleted, remove resources but keep DB record"""
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    errors = []
    
    try:
        # 1. Delete Kubernetes namespace
        try:
            namespace_cmd = f"kubectl delete namespace {service.namespace} --ignore-not-found=true"
            result = subprocess.run(
                namespace_cmd.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0 and "not found" not in result.stderr.lower():
                errors.append(f"Namespace deletion warning: {result.stderr}")
        except Exception as e:
            errors.append(f"Failed to delete namespace: {str(e)}")
        
        # 2. Delete ArgoCD Application
        try:
            argocd_app_name = service.name.lower()
            argocd_cmd = f"kubectl delete application {argocd_app_name} -n argocd --ignore-not-found=true"
            result = subprocess.run(
                argocd_cmd.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0 and "not found" not in result.stderr.lower():
                errors.append(f"ArgoCD app deletion warning: {result.stderr}")
        except Exception as e:
            errors.append(f"Failed to delete ArgoCD app: {str(e)}")
        
        # 3. Soft Delete in DB
        service.deleted_at = datetime.now()
        service.status = "deleted"
        await session.commit()
        
        return {
            "message": "Service deleted successfully",
            "warnings": errors if errors else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during deletion: {str(e)}. Warnings: {errors}"
        )

@router.websocket("/ws/{service_id}/logs")
async def service_logs_websocket(websocket: WebSocket, service_id: str, session: AsyncSession = Depends(get_session)):
    """WebSocket endpoint for real-time service creation logs"""
    await manager.connect(websocket, service_id)
    
    try:
        # Send connection acknowledgment
        await websocket.send_json({
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": "Connected to log stream",
            "step": "connection"
        })
        
        # Send existing logs from DB first
        result = await session.execute(select(Service).where(Service.id == service_id))
        service = result.scalars().first()
        
        if service:
            for log in service.logs:
                await websocket.send_json(log)
        
        # Keep connection open for new logs
        while True:
            await websocket.receive_text() # Keep alive
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, service_id)
