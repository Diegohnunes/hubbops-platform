"""
Configuration API endpoints

Provides endpoints to check platform configuration status
and integration health, and to update configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
import subprocess
import logging
import yaml
import os
from pathlib import Path

from app.core.config import Settings, get_config
from app.api.auth import require_admin
from app.models.auth import User

router = APIRouter(prefix="/config", tags=["config"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_config_status(config: Settings = Depends(get_config)) -> Dict[str, Any]:
    """
    Get current configuration status and integration health.
    
    Returns non-sensitive configuration values and validates
    that required integrations are properly configured.
    """
    issues = config.validate()
    
    # Check integration connectivity
    integrations_status = await check_integrations(config)
    
    return {
        "config": config.to_safe_dict(),
        "issues": issues,
        "integrations": integrations_status,
    }


@router.get("/integrations")
async def check_integration_health(config: Settings = Depends(get_config)) -> Dict[str, Any]:
    """Check health of all configured integrations"""
    return await check_integrations(config)


class ConfigUpdateRequest(BaseModel):
    docker_registry: Optional[str] = None
    git_provider: Optional[str] = None
    git_apps_repo: Optional[str] = None
    git_infra_repo: Optional[str] = None
    ssh_private_key: Optional[str] = None
    grafana_enabled: Optional[bool] = None
    argocd_enabled: Optional[bool] = None
    prometheus_enabled: Optional[bool] = None


@router.patch("/", response_model=Dict[str, Any])
async def update_config(
    request: ConfigUpdateRequest,
    user: User = Depends(require_admin),
    config: Settings = Depends(get_config)
):
    """
    Update platform configuration.
    Persists changes to /data/config/settings.yaml.
    """
    # Determine config path
    config_dir = Path("/data/config")
    if not config_dir.exists():
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to /app/config if /data is not writable (e.g. local dev)
            config_dir = Path("/app/config")
    
    settings_path = config_dir / "settings.yaml"
    
    # Load existing yaml or create empty
    current_yaml = {}
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                current_yaml = yaml.safe_load(f) or {}
        except Exception:
            pass
    
    # Update values
    if request.docker_registry is not None:
        if "docker" not in current_yaml: current_yaml["docker"] = {}
        current_yaml["docker"]["registry"] = request.docker_registry
        
    if request.git_provider is not None:
        if "git" not in current_yaml: current_yaml["git"] = {}
        current_yaml["git"]["provider"] = request.git_provider
        
    if request.git_apps_repo is not None:
        if "git" not in current_yaml: current_yaml["git"] = {}
        if "repositories" not in current_yaml["git"]: current_yaml["git"]["repositories"] = {}
        if "apps" not in current_yaml["git"]["repositories"]: current_yaml["git"]["repositories"]["apps"] = {}
        current_yaml["git"]["repositories"]["apps"]["url"] = request.git_apps_repo
        
    if request.git_infra_repo is not None:
        if "git" not in current_yaml: current_yaml["git"] = {}
        if "repositories" not in current_yaml["git"]: current_yaml["git"]["repositories"] = {}
        if "infrastructure" not in current_yaml["git"]["repositories"]: current_yaml["git"]["repositories"]["infrastructure"] = {}
        current_yaml["git"]["repositories"]["infrastructure"]["url"] = request.git_infra_repo

    if request.ssh_private_key is not None:
        # Save SSH key to /data/ssh/id_rsa
        ssh_dir = Path("/data/ssh")
        if not ssh_dir.exists():
            try:
                ssh_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        
        ssh_key_path = ssh_dir / "id_rsa"
        try:
            # Ensure directory permissions are secure if possible (though inside container usually root)
            if ssh_dir.exists():
                os.chmod(ssh_dir, 0o700)
                
            with open(ssh_key_path, "w") as f:
                f.write(request.ssh_private_key)
                if not request.ssh_private_key.endswith('\n'):
                    f.write('\n')
            
            os.chmod(ssh_key_path, 0o600)
            
            # Apply immediately for current process
            os.environ["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
            logger.info(f"Updated GIT_SSH_COMMAND to use key at {ssh_key_path}")
            
        except Exception as e:
            logger.error(f"Failed to save SSH key: {e}")
            # Don't fail the whole request, but maybe warn?
            pass

    if request.grafana_enabled is not None:
        if "integrations" not in current_yaml: current_yaml["integrations"] = {}
        if "grafana" not in current_yaml["integrations"]: current_yaml["integrations"]["grafana"] = {}
        current_yaml["integrations"]["grafana"]["enabled"] = request.grafana_enabled

    if request.argocd_enabled is not None:
        if "integrations" not in current_yaml: current_yaml["integrations"] = {}
        if "argocd" not in current_yaml["integrations"]: current_yaml["integrations"]["argocd"] = {}
        current_yaml["integrations"]["argocd"]["enabled"] = request.argocd_enabled

    if request.prometheus_enabled is not None:
        if "integrations" not in current_yaml: current_yaml["integrations"] = {}
        if "prometheus" not in current_yaml["integrations"]: current_yaml["integrations"]["prometheus"] = {}
        current_yaml["integrations"]["prometheus"]["enabled"] = request.prometheus_enabled
        
    # Save to file
    try:
        with open(settings_path, "w") as f:
            yaml.dump(current_yaml, f, default_flow_style=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")
        
    return {"message": "Configuration saved. Please restart the backend to apply changes fully.", "path": str(settings_path)}


async def check_integrations(config: Settings) -> Dict[str, Any]:
    """Check connectivity to configured integrations"""
    status = {}
    
    # Check ArgoCD
    if config.ARGOCD_ENABLED:
        status["argocd"] = await check_argocd(config.ARGOCD_NAMESPACE)
    
    # Check Grafana
    if config.GRAFANA_ENABLED:
        status["grafana"] = await check_grafana(config.GRAFANA_NAMESPACE, config.GRAFANA_URL)
    
    # Check Prometheus
    if config.PROMETHEUS_ENABLED:
        status["prometheus"] = await check_prometheus(config.PROMETHEUS_URL)
    
    # Check Git configuration
    status["git"] = check_git_config(config)
    
    return status


async def check_argocd(namespace: str) -> Dict[str, Any]:
    """Check ArgoCD server connectivity"""
    try:
        result = subprocess.run(
            ["kubectl", "get", "applications", "-n", namespace, "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            app_count = len([l for l in result.stdout.strip().split('\n') if l])
            return {
                "status": "connected",
                "applications": app_count
            }
        else:
            return {
                "status": "error",
                "message": result.stderr.strip()[:100]
            }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "kubectl command timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:100]}


async def check_grafana(namespace: str, url: str) -> Dict[str, Any]:
    """Check Grafana connectivity"""
    try:
        # Try to get Grafana service
        result = subprocess.run(
            ["kubectl", "get", "svc", "-n", namespace, "-l", "app.kubernetes.io/name=grafana", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "connected", "in_cluster": True}
        elif url:
            return {"status": "configured", "url": url}
        else:
            return {"status": "not_found", "message": "Grafana service not found in cluster"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:100]}


async def check_prometheus(url: str) -> Dict[str, Any]:
    """Check Prometheus connectivity"""
    try:
        result = subprocess.run(
            ["kubectl", "get", "svc", "-n", "monitoring", "-l", "app.kubernetes.io/name=prometheus", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "connected", "in_cluster": True}
        elif url:
            return {"status": "configured", "url": url}
        else:
            return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:100]}


def check_git_config(config: Settings) -> Dict[str, Any]:
    """Check Git configuration status"""
    return {
        "provider": config.GIT_PROVIDER,
        "apps_repo": {
            "configured": bool(config.GIT_APPS_REPO),
        },
        "infra_repo": {
            "configured": bool(config.GIT_INFRA_REPO),
        }
    }
