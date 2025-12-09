"""
HubbOps Configuration

Loads configuration from environment variables and YAML files.
Priority: Environment variables > secrets.yaml > settings.yaml > defaults
"""

import os
import yaml
from typing import Any, Optional
from pathlib import Path
from functools import lru_cache
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Settings(BaseSettings):
    """Configuration settings from environment and YAML files"""
    
    # API Settings
    API_TITLE: str = "Hubbops API"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Paths
    OPS_CLI_PATH: str = "/app/ops-cli"
    TEMPLATES_PATH: str = "/app/public/templates"
    CONFIG_DIR: str = "/app/config"
    
    # Kubernetes
    K3D_CLUSTER_NAME: str = "devlab"
    KUBECONFIG_PATH: Optional[str] = None
    DEFAULT_NAMESPACE: str = "default"
    
    # Docker
    DOCKER_REGISTRY: str = "local"
    
    # Git
    GIT_PROVIDER: str = "github"
    GIT_APPS_REPO: str = ""
    GIT_INFRA_REPO: str = ""
    GIT_SSH_KEY_NAME: str = ""
    
    # Integrations
    GRAFANA_ENABLED: bool = True
    GRAFANA_URL: str = ""
    GRAFANA_NAMESPACE: str = "monitoring"
    ARGOCD_ENABLED: bool = True
    ARGOCD_NAMESPACE: str = "argocd"
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_URL: str = ""
    
    # Auth
    AUTH_ENABLED: bool = False
    JWT_SECRET: str = ""
    TOKEN_EXPIRY_HOURS: int = 24
    ALLOW_REGISTRATION: bool = False
    DEFAULT_ADMIN_EMAIL: str = "admin@hubbops.local"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = "HUBBOPS_"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
    
    def _find_config_dir(self) -> Path:
        """Find the config directory"""
        if self.CONFIG_DIR:
            path = Path(self.CONFIG_DIR)
            if path.exists():
                return path
        
        possible_paths = [
            Path("/data/config"),  # Persistent storage (highest priority)
            Path("/app/config"),
            Path(__file__).parent.parent.parent.parent / "config",
            Path.cwd() / "config",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return Path("/app/config")
    
    def _load_yaml_config(self):
        """Load additional config from YAML files"""
        config_dir = self._find_config_dir()
        
        # Load settings.yaml
        for filename in ["settings.yaml", "settings.example.yaml"]:
            settings_path = config_dir / filename
            if settings_path.exists():
                try:
                    with open(settings_path) as f:
                        yaml_config = yaml.safe_load(f) or {}
                    self._apply_yaml_config(yaml_config)
                    logger.info(f"Loaded config from {settings_path}")
                    break
                except Exception as e:
                    logger.warning(f"Error loading {settings_path}: {e}")
        
        # Load secrets.yaml
        secrets_path = config_dir / "secrets.yaml"
        if secrets_path.exists():
            try:
                with open(secrets_path) as f:
                    secrets = yaml.safe_load(f) or {}
                self._apply_yaml_secrets(secrets)
                logger.info(f"Loaded secrets from {secrets_path}")
            except Exception as e:
                logger.warning(f"Error loading secrets: {e}")
    
    def _apply_yaml_config(self, config: dict):
        """Apply YAML config values (only if not already set via env)"""
        mappings = {
            ("docker", "registry"): "DOCKER_REGISTRY",
            ("docker", "k3d_cluster"): "K3D_CLUSTER_NAME",
            ("git", "provider"): "GIT_PROVIDER",
            ("git", "repositories", "apps", "url"): "GIT_APPS_REPO",
            ("git", "repositories", "infrastructure", "url"): "GIT_INFRA_REPO",
            ("kubernetes", "default_namespace"): "DEFAULT_NAMESPACE",
            ("integrations", "grafana", "enabled"): "GRAFANA_ENABLED",
            ("integrations", "grafana", "url"): "GRAFANA_URL",
            ("integrations", "grafana", "namespace"): "GRAFANA_NAMESPACE",
            ("integrations", "argocd", "enabled"): "ARGOCD_ENABLED",
            ("integrations", "argocd", "namespace"): "ARGOCD_NAMESPACE",
            ("integrations", "prometheus", "enabled"): "PROMETHEUS_ENABLED",
            ("integrations", "prometheus", "url"): "PROMETHEUS_URL",
            ("auth", "enabled"): "AUTH_ENABLED",
            ("auth", "jwt_secret"): "JWT_SECRET",
            ("auth", "token_expiry_hours"): "TOKEN_EXPIRY_HOURS",
            ("auth", "allow_registration"): "ALLOW_REGISTRATION",
            ("auth", "default_admin_email"): "DEFAULT_ADMIN_EMAIL",
            ("logging", "level"): "LOG_LEVEL",
        }
        
        for yaml_path, attr_name in mappings.items():
            # Don't override if already set via environment
            env_key = f"HUBBOPS_{attr_name}"
            if os.getenv(env_key):
                continue
            
            # Navigate YAML structure
            value = config
            for key in yaml_path:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            
            if value is not None:
                setattr(self, attr_name, value)
    
    def _apply_yaml_secrets(self, secrets: dict):
        """Apply secrets from YAML"""
        if jwt := secrets.get("auth", {}).get("jwt_secret"):
            if not os.getenv("HUBBOPS_JWT_SECRET"):
                self.JWT_SECRET = jwt
    
    def get_ssh_key(self, name: str) -> Optional[str]:
        """Get SSH key from secrets file"""
        config_dir = self._find_config_dir()
        secrets_path = config_dir / "secrets.yaml"
        if secrets_path.exists():
            with open(secrets_path) as f:
                secrets = yaml.safe_load(f) or {}
            return secrets.get("ssh_keys", {}).get(name)
        return None
    
    def get_grafana_token(self) -> Optional[str]:
        """Get Grafana service account token"""
        config_dir = self._find_config_dir()
        secrets_path = config_dir / "secrets.yaml"
        if secrets_path.exists():
            with open(secrets_path) as f:
                secrets = yaml.safe_load(f) or {}
            return secrets.get("grafana", {}).get("service_account_token")
        return None
    
    def to_safe_dict(self) -> dict:
        """Export non-sensitive config as dictionary"""
        return {
            "platform": {
                "name": "HubbOps",
                "version": self.API_VERSION,
            },
            "docker": {
                "registry": self.DOCKER_REGISTRY,
                "k3d_cluster": self.K3D_CLUSTER_NAME,
            },
            "git": {
                "provider": self.GIT_PROVIDER,
                "apps_configured": bool(self.GIT_APPS_REPO),
                "infra_configured": bool(self.GIT_INFRA_REPO),
            },
            "integrations": {
                "grafana": {"enabled": self.GRAFANA_ENABLED},
                "argocd": {"enabled": self.ARGOCD_ENABLED},
                "prometheus": {"enabled": self.PROMETHEUS_ENABLED},
            },
            "auth": {
                "enabled": self.AUTH_ENABLED,
            }
        }
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        if self.AUTH_ENABLED and not self.JWT_SECRET:
            issues.append("ERROR: JWT_SECRET is required when auth is enabled")
        
        if not self.DOCKER_REGISTRY or self.DOCKER_REGISTRY == "local":
            issues.append("INFO: Using local Docker registry")
        
        if self.ARGOCD_ENABLED and not self.GIT_INFRA_REPO:
            issues.append("WARNING: GIT_INFRA_REPO not configured (required for ArgoCD GitOps)")
        
        return issues


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Alias for backward compatibility and dependency injection
settings = get_settings()


def get_config() -> Settings:
    """Dependency injection for FastAPI"""
    return get_settings()
