"""
Orchestrateur central de l'Agent OS BARBATOS.
Coordonne le cycle de vie de tous les modules (Audio, Vision, Système, Brain, Réseau, UI).
"""

import asyncio
import logging
from typing import Optional
from config.settings import settings
from core.bus import event_bus, Event
from core.state import state_manager, AgentState
from core.memory import short_term_memory, long_term_memory
from ai.brain import brain
from ai.tools_registry import tools_registry
from audio.listener import audio_listener
from audio.tts import tts
from vision.camera import camera_manager
from automation.scheduler import scheduler
from automation.watchers import hardware_watcher

logger = logging.getLogger("Barbatos.Agent")


class BarbatosAgent:
    """Agent IA local autonome BARBATOS."""

    def __init__(self):
        self.name = settings.system.name
        self.version = settings.system.version
        self.is_running = False
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Abonne l'agent aux événements clés du bus."""
        event_bus.subscribe("audio.command_received", self._handle_voice_command)
        event_bus.subscribe("system.alert.high_cpu", self._handle_high_cpu_alert)
        event_bus.subscribe("agent.final_answer", self._handle_final_answer)

    async def _handle_voice_command(self, event: Event):
        """Traite une commande vocale captée par le micro."""
        command = event.data.get("command", "")
        if command:
            logger.info(f"[VOIX] Commande reçue : {command}")
            await self.process_command(command, source="voice")

    async def _handle_high_cpu_alert(self, event: Event):
        """Alerte CPU élevée."""
        data = event.data or {}
        logger.warning(f"[ALERTE] Charge CPU critique : {data.get('cpu_percent')}%")

    async def _handle_final_answer(self, event: Event):
        """Lit la réponse finale avec le TTS si le mode audio est activé."""
        answer = event.data.get("answer", "")
        if settings.audio.enabled and answer:
            tts.speak(answer)

    async def process_command(self, user_command: str, source: str = "text") -> str:
        """Traite une instruction utilisateur via le Brain autonome."""
        logger.info(f"[{source.upper()}] Traitement : '{user_command}'")
        answer = await brain.think_and_act(user_command)
        return answer

    async def start(self, enable_audio: bool = False, enable_vision: bool = False):
        """Démarre le système d'exploitation de l'agent et ses services de fond."""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"=== Démarrage de {self.name} v{self.version} ===")

        # 1. Démarrage du planificateur
        await scheduler.start()

        # 2. Démarrage de la surveillance matérielle
        await hardware_watcher.start()

        # 3. Démarrage optionnel du module vocal
        if enable_audio and settings.audio.enabled:
            audio_listener.start()

        # 4. Démarrage optionnel de la caméra
        if enable_vision and settings.vision.enabled:
            camera_manager.start_capture()

        await state_manager.set_state(AgentState.IDLE, "Système prêt et opérationnel")
        await event_bus.publish("agent.started", {"name": self.name, "version": self.version})

    async def stop(self):
        """Arrêt propre de l'agent et libération des ressources."""
        self.is_running = False
        logger.info(f"Arrêt de {self.name}...")

        audio_listener.stop()
        camera_manager.stop()
        hardware_watcher.stop()
        scheduler.stop()
        tts.stop()

        await state_manager.set_state(AgentState.IDLE, "Système éteint")
        await event_bus.publish("agent.stopped", {"name": self.name})


barbatos = BarbatosAgent()
