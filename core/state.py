"""
Machine à états et gestionnaire de statut pour l'Agent Barbatos.
"""

from enum import Enum
import time
from typing import Any, Dict, Optional
from core.bus import event_bus


class AgentState(str, Enum):
    IDLE = "IDLE"              # En attente de commande
    LISTENING = "LISTENING"    # Micro actif / écoute de commande vocale
    THINKING = "THINKING"      # Analyse LLM / raisonnement ReAct / planification
    EXECUTING = "EXECUTING"    # Exécution d'une action système, d'un outil ou d'un workflow
    ADAPTING = "ADAPTING"      # Réajustement suite à un résultat inattendu
    ERROR = "ERROR"            # Erreur nécessitant attention ou notification


class StateManager:
    """Gère l'état courant de l'agent et notifie le bus d'événements."""

    def __init__(self):
        self._current_state: AgentState = AgentState.IDLE
        self._last_state: AgentState = AgentState.IDLE
        self._current_activity: str = "En veille"
        self._start_time: float = time.time()
        self._tasks_completed: int = 0
        self._last_state_change: float = time.time()

    @property
    def state(self) -> AgentState:
        return self._current_state

    @property
    def activity(self) -> str:
        return self._current_activity

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    async def set_state(self, new_state: AgentState, activity_detail: str = ""):
        """Modifie l'état de l'agent et diffuse l'événement."""
        if self._current_state != new_state or activity_detail != self._current_activity:
            self._last_state = self._current_state
            self._current_state = new_state
            self._current_activity = activity_detail or f"État: {new_state.value}"
            self._last_state_change = time.time()

            await event_bus.publish(
                topic="agent.state_changed",
                data={
                    "state": self._current_state.value,
                    "last_state": self._last_state.value,
                    "activity": self._current_activity,
                    "timestamp": time.time(),
                },
                sender="state_manager"
            )

    def record_task_completed(self):
        self._tasks_completed += 1

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "state": self._current_state.value,
            "activity": self._current_activity,
            "uptime_seconds": round(self.uptime_seconds, 1),
            "tasks_completed": self._tasks_completed,
            "seconds_in_current_state": round(time.time() - self._last_state_change, 1),
        }


state_manager = StateManager()
