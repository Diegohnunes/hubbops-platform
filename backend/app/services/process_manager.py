import asyncio
import logging
from typing import List, Dict
from fastapi import WebSocket
from datetime import datetime
import json
import os
import re

from app.core.db import engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service import Service
from sqlmodel import select

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Map service_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, service_id: str):
        await websocket.accept()
        if service_id not in self.active_connections:
            self.active_connections[service_id] = []
        self.active_connections[service_id].append(websocket)

    def disconnect(self, websocket: WebSocket, service_id: str):
        if service_id in self.active_connections:
            if websocket in self.active_connections[service_id]:
                self.active_connections[service_id].remove(websocket)
            if not self.active_connections[service_id]:
                del self.active_connections[service_id]

    async def broadcast(self, message: dict, service_id: str):
        if service_id in self.active_connections:
            for connection in self.active_connections[service_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")

manager = ConnectionManager()

class ProcessManager:
    @staticmethod
    async def run_command(command: str, service_id: str, cwd: str = None):
        """
        Run a shell command and stream output to WebSockets and DB.
        """
        logger.info(f"Starting command for service {service_id}: {command}")
        
        # Initial log
        await ProcessManager._log(service_id, "info", f"Starting command: {command}")
        
        # Small delay to allow WebSocket clients to connect
        await asyncio.sleep(0.5)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            # Read stdout and stderr concurrently
            await asyncio.gather(
                ProcessManager._read_stream(process.stdout, service_id, "info"),
                ProcessManager._read_stream(process.stderr, service_id, "error")
            )

            return_code = await process.wait()
            
            if return_code == 0:
                await ProcessManager._log(service_id, "success", "Command completed successfully")
                await ProcessManager._update_status(service_id, "active")
            else:
                await ProcessManager._log(service_id, "error", f"Command failed with exit code {return_code}")
                await ProcessManager._update_status(service_id, "failed")

        except Exception as e:
            logger.error(f"Error running command: {e}")
            await ProcessManager._log(service_id, "error", f"Internal error: {str(e)}")
            await ProcessManager._update_status(service_id, "failed")

    @staticmethod
    async def _read_stream(stream, service_id: str, default_level: str):
        current_step = None
        while True:
            line = await stream.readline()
            if not line:
                break
            message = line.decode().strip()
            if message:
                # Parse step
                # Example: Step 1/10: Generating application code...
                step_match = re.search(r"Step \d+/\d+: (.*)", message)
                if step_match:
                    # Clean up step name (remove trailing ...)
                    current_step = step_match.group(1).strip().rstrip(".")
                
                # Parse level based on emojis or keywords
                level = default_level
                if "⚠️" in message:
                    level = "warning"
                elif "❌" in message:
                    level = "error"
                elif "✅" in message:
                    level = "success"
                
                await ProcessManager._log(service_id, level, message, step=current_step)

    @staticmethod
    async def _log(service_id: str, level: str, message: str, step: str = None):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "step": step
        }
        
        # Broadcast to WebSockets
        await manager.broadcast(log_entry, service_id)
        
        # Persist to DB
        try:
            async with AsyncSession(engine) as session:
                statement = select(Service).where(Service.id == service_id)
                results = await session.execute(statement)
                service = results.scalars().first()
                if service:
                    current_logs = service.logs
                    current_logs.append(log_entry)
                    service.logs = current_logs
                    session.add(service)
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist log: {e}")

    @staticmethod
    async def _update_status(service_id: str, status: str):
        try:
            async with AsyncSession(engine) as session:
                statement = select(Service).where(Service.id == service_id)
                results = await session.execute(statement)
                service = results.scalars().first()
                if service:
                    service.status = status
                    session.add(service)
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
