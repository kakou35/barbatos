"""
Serveur API local FastAPI et WebSockets pour BARBATOS.
Fournit une interface REST et temps réel pour piloter l'agent et alimenter le Web HUD.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from config.settings import settings
from core.bus import event_bus, Event
from core.state import state_manager
from core.memory import short_term_memory, long_term_memory
from ai.brain import brain
from ai.tools_registry import tools_registry
from system.windows_ops import windows_ops

logger = logging.getLogger("Barbatos.API")

app = FastAPI(title="BARBATOS Agent OS API", version="1.0.0")

# Gestionnaire de connexions WebSockets multiples
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


# Pont entre EventBus et WebSockets pour streaming des événements en temps réel
async def forward_event_to_websocket(event: Event):
    await ws_manager.broadcast({
        "type": "event",
        "topic": event.topic,
        "sender": event.sender,
        "data": event.data,
        "timestamp": event.timestamp.isoformat()
    })

event_bus.subscribe("*", forward_event_to_websocket)


# Modèles de requêtes
class ChatRequest(BaseModel):
    message: str


class ToolExecutionRequest(BaseModel):
    arguments: Dict[str, Any] = {}


# --- Routes REST ---

@app.get("/api/status")
async def get_system_status():
    """Retourne l'état complet de l'agent et du système."""
    return {
        "agent": state_manager.get_status_summary(),
        "hardware": windows_ops.get_hardware_metrics(),
        "config": {
            "model": settings.ai.model,
            "provider": settings.ai.provider,
            "vision_enabled": settings.vision.enabled,
            "audio_enabled": settings.audio.enabled,
        }
    }


@app.post("/api/chat")
async def post_chat(req: ChatRequest):
    """Envoie un message à l'agent et attend la réponse du Brain."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message vide")

    answer = await brain.think_and_act(req.message)
    return {"message": req.message, "answer": answer}


@app.get("/api/tools")
async def list_tools():
    """Liste tous les outils disponibles."""
    return tools_registry.list_tools()


@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str, req: ToolExecutionRequest):
    """Invoque un outil directement."""
    result = await tools_registry.execute_tool(tool_name, req.arguments)
    return {"tool": tool_name, "result": result}


@app.get("/api/events")
async def get_recent_events(limit: int = 40):
    """Retourne l'historique récent des événements du bus."""
    return event_bus.get_recent_events(limit=limit)


# --- Route WebSocket temps réel ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Envoi de l'état initial
    await websocket.send_json({
        "type": "status_init",
        "status": state_manager.get_status_summary(),
        "hardware": windows_ops.get_hardware_metrics()
    })

    try:
        while True:
            data = await websocket.receive_json()
            # Si le client envoie une commande via WebSocket
            if data.get("type") == "user_command":
                user_text = data.get("text", "")
                if user_text:
                    # Lancement asynchrone pour ne pas bloquer la socket
                    asyncio.create_task(brain.think_and_act(user_text))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket : {e}")
        ws_manager.disconnect(websocket)


# Servir le Dashboard Web HUD
static_dir = Path(__file__).resolve().parent.parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_hud():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return "<h1>BARBATOS HUD Dashboard en cours de chargement...</h1>"
