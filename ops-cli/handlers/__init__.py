"""Handlers package init"""

from .base import BaseHandler, ServiceConfig
from .python_service import PythonServiceHandler
from .go_service import GoServiceHandler

# Register all handlers
HANDLERS = {
    "python-service": PythonServiceHandler,
    "go-service": GoServiceHandler,
    # Add more handlers as needed:
    # "crypto-collector": CryptoCollectorHandler,
}


def get_handler(template_id: str, service_config: ServiceConfig) -> BaseHandler:
    """Get the appropriate handler for a template"""
    handler_class = HANDLERS.get(template_id)
    if not handler_class:
        raise ValueError(f"No handler registered for template: {template_id}")
    return handler_class(service_config)


def list_supported_templates() -> list[str]:
    """List all supported template IDs"""
    return list(HANDLERS.keys())

