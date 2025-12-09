from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from pathlib import Path

from app.schemas.service import TemplateBase, TemplateDetail
from app.core.config import settings

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/", response_model=List[TemplateDetail])
async def list_templates():
    """List all available templates"""
    templates_file = Path(settings.TEMPLATES_PATH) / "templates.json"
    
    if not templates_file.exists():
        raise HTTPException(status_code=404, detail="Templates file not found")
    
    with open(templates_file, 'r') as f:
        data = json.load(f)
    
    return data.get("templates", [])

@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """Get details of a specific template including schema"""
    templates_file = Path(settings.TEMPLATES_PATH) / "templates.json"
    
    if not templates_file.exists():
        raise HTTPException(status_code=404, detail="Templates file not found")
    
    with open(templates_file, 'r') as f:
        data = json.load(f)
    
    templates = data.get("templates", [])
    template = next((t for t in templates if t["id"] == template_id), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Load schema if available
    if template.get("schema"):
        schema_file = Path(settings.TEMPLATES_PATH) / template["schema"].lstrip("/templates/")
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                template["schema_data"] = json.load(f)
    
    return template
