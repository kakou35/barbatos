"""
EventBus asynchrone pour la communication inter-processus et inter-modules dans BARBATOS.
Permet un couplage faible entre le Brain, le Système, l'Audio, la Vision et l'UI.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional
import uuid

logger = logging.getLogger("Barbatos.EventBus")


@dataclass
class Event:
    topic: str
    data: Any = None
    sender: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "topic": self.topic,
            "data": self.data,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
        }


class EventBus:
    """Bus d'événements asynchrone centralisé."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Coroutine[Any, Any, None]]]] = {}
        self._wildcard_subscribers: List[Callable[[Event], Coroutine[Any, Any, None]]] = []
        self._history: List[Event] = []
        self._max_history = 200
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, handler: Callable[[Event], Coroutine[Any, Any, None]]):
        """Souscrit une coroutine à un topic précis ou '*' pour tous."""
        if topic == "*":
            if handler not in self._wildcard_subscribers:
                self._wildcard_subscribers.append(handler)
        else:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Callable[[Event], Coroutine[Any, Any, None]]):
        """Désabonne un handler."""
        if topic == "*" and handler in self._wildcard_subscribers:
            self._wildcard_subscribers.remove(handler)
        elif topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)

    async def publish(self, topic: str, data: Any = None, sender: str = "core") -> Event:
        """Publie un événement et notifie tous les abonnés de manière asynchrone."""
        event = Event(topic=topic, data=data, sender=sender)

        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        handlers = list(self._subscribers.get(topic, [])) + list(self._wildcard_subscribers)
        
        # Exécution non-bloquante de tous les abonnés
        tasks = []
        for handler in handlers:
            try:
                tasks.append(asyncio.create_task(self._safe_call(handler, event)))
            except Exception as e:
                logger.error(f"Erreur déclenchement handler pour {topic}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return event

    async def _safe_call(self, handler: Callable[[Event], Coroutine[Any, Any, None]], event: Event):
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Erreur dans le handler d'événement '{event.topic}': {e}", exc_info=True)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les derniers événements au format dict."""
        return [e.to_dict() for e in self._history[-limit:]]


# Instance globale du bus d'événements
event_bus = EventBus()
