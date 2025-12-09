import pytest
from app.core.config import Settings

def test_settings_load_defaults():
    """Test that settings load with default values"""
    settings = Settings()
    assert settings.API_TITLE == "HubbOps Platform API"
    assert settings.API_VERSION == "1.0.0"
    assert settings.AUTH_ENABLED is True

def test_settings_validation():
    """Test settings validation logic"""
    settings = Settings()
    
    # Should warn about missing registry
    settings.DOCKER_REGISTRY = ""
    issues = settings.validate()
    assert any("DOCKER_REGISTRY" in issue for issue in issues)
    
    # Should warn about default secret
    settings.JWT_SECRET = ""
    issues = settings.validate()
    assert any("JWT_SECRET" in issue for issue in issues)

def test_image_name_generation():
    """Test Docker image name generation"""
    settings = Settings()
    settings.DOCKER_REGISTRY = "myreg"
    
    image = settings.get_image_name("myservice", "v1")
    assert image == "myreg/myservice:v1"
    
    # Test with local registry
    settings.DOCKER_REGISTRY = "local"
    image = settings.get_image_name("myservice", "v1")
    assert image == "myservice:v1"
