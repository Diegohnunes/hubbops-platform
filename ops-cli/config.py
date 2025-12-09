"""
Configuration loader for ops-cli

Loads settings from config/settings.yaml and config/secrets.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Optional


class OpsConfig:
    """Configuration for ops-cli commands"""
    
    def __init__(self):
        self._config = {}
        self._secrets = {}
        self._load()
    
    def _find_config_dir(self) -> Path:
        """Find config directory"""
        # Environment variable
        if env_path := os.getenv("HUBBOPS_CONFIG_DIR"):
            return Path(env_path)
        
        # Relative to ops-cli
        base = Path(__file__).parent.parent.parent
        config_path = base / "config"
        if config_path.exists():
            return config_path
        
        # Current directory
        if Path("config").exists():
            return Path("config")
        
        return Path("config")
    
    def _load(self):
        """Load configuration files"""
        config_dir = self._find_config_dir()
        
        # Load settings
        for filename in ["settings.yaml", "settings.example.yaml"]:
            path = config_dir / filename
            if path.exists():
                with open(path) as f:
                    self._config = yaml.safe_load(f) or {}
                break
        
        # Load secrets
        secrets_path = config_dir / "secrets.yaml"
        if secrets_path.exists():
            with open(secrets_path) as f:
                self._secrets = yaml.safe_load(f) or {}
    
    def _get(self, data: dict, *keys, default=None):
        """Get nested value"""
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
    
    @property
    def docker_registry(self) -> str:
        """Docker registry for images (e.g., 'myorg' or 'ghcr.io/myorg')"""
        return os.getenv("HUBBOPS_DOCKER_REGISTRY") or \
               self._get(self._config, "docker", "registry", default="local")
    
    @property
    def k3d_cluster(self) -> str:
        """k3d cluster name"""
        return os.getenv("HUBBOPS_K3D_CLUSTER") or \
               self._get(self._config, "docker", "k3d_cluster", default="devlab")
    
    @property
    def git_apps_repo(self) -> str:
        """Git repository for application code"""
        return os.getenv("HUBBOPS_GIT_APPS_REPO") or \
               self._get(self._config, "git", "repositories", "apps", "url", default="")
    
    @property
    def git_infra_repo(self) -> str:
        """Git repository for infrastructure/GitOps"""
        return os.getenv("HUBBOPS_GIT_INFRA_REPO") or \
               self._get(self._config, "git", "repositories", "infrastructure", "url", default="")
    
    @property
    def default_namespace(self) -> str:
        """Default Kubernetes namespace"""
        return os.getenv("HUBBOPS_DEFAULT_NAMESPACE") or \
               self._get(self._config, "kubernetes", "default_namespace", default="default")
    
    @property
    def grafana_url(self) -> str:
        """Grafana URL"""
        return os.getenv("HUBBOPS_GRAFANA_URL") or \
               os.getenv("GRAFANA_URL") or \
               self._get(self._config, "integrations", "grafana", "url", default="http://localhost:3000")
    
    @property
    def grafana_enabled(self) -> bool:
        """Is Grafana integration enabled"""
        return self._get(self._config, "integrations", "grafana", "enabled", default=True)
    
    @property
    def argocd_enabled(self) -> bool:
        """Is ArgoCD integration enabled"""
        return self._get(self._config, "integrations", "argocd", "enabled", default=True)
    
    def get_image_name(self, service_name: str, tag: str = "v1.0") -> str:
        """Get full image name for a service"""
        if self.docker_registry and self.docker_registry != "local":
            return f"{self.docker_registry}/{service_name}:{tag}"
        return f"{service_name}:{tag}"
    
    def validate(self) -> list[str]:
        """Validate configuration"""
        issues = []
        
        if not self.git_apps_repo:
            issues.append("WARNING: git.repositories.apps.url not configured")
        
        if not self.git_infra_repo:
            issues.append("WARNING: git.repositories.infrastructure.url not configured")
        
        return issues


# Singleton instance
_config = None

def get_config() -> OpsConfig:
    """Get or create config instance"""
    global _config
    if _config is None:
        _config = OpsConfig()
    return _config
