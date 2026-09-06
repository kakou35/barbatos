"""
Planificateur de tâches récurrentes et programmées (Cron local) pour BARBATOS.
Permet d'exécuter des actions, workflows ou commandes à intervalle régulier.
"""

import asyncio
import logging
import time
from typing import Callable, Coroutine, Dict, Any, List, Optional
import uuid

logger = logging.getLogger("Barbatos.Scheduler")


class ScheduledTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        interval_seconds: int,
        coro_func: Callable[[], Coroutine[Any, Any, None]],
        repeat: bool = True
    ):
        self.task_id = task_id
        self.name = name
        self.interval_seconds = interval_seconds
        self.coro_func = coro_func
        self.repeat = repeat
        self.last_run = 0.0
        self.run_count = 0


class LocalScheduler:
    """Ordonnanceur asynchrone non-bloquant."""

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

    def add_interval_task(
        self,
        name: str,
        interval_seconds: int,
        coro_func: Callable[[], Coroutine[Any, Any, None]],
        repeat: bool = True
    ) -> str:
        """Enregistre une tâche récurrente toutes les N secondes."""
        task_id = str(uuid.uuid4())[:8]
        task = ScheduledTask(task_id, name, interval_seconds, coro_func, repeat)
        self._tasks[task_id] = task
        logger.info(f"Tâche planifiée enregistrée : '{name}' (intervalle : {interval_seconds}s)")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": t.task_id,
                "name": t.name,
                "interval_seconds": t.interval_seconds,
                "run_count": t.run_count,
                "last_run": t.last_run
            }
            for t in self._tasks.values()
        ]

    async def start(self):
        """Démarre la boucle de planification."""
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        while self._running:
            now = time.time()
            to_remove = []

            for task_id, task in list(self._tasks.items()):
                if now - task.last_run >= task.interval_seconds:
                    task.last_run = now
                    task.run_count += 1
                    try:
                        asyncio.create_task(task.coro_func())
                    except Exception as e:
                        logger.error(f"Erreur exécution tâche {task.name}: {e}")

                    if not task.repeat:
                        to_remove.append(task_id)

            for tid in to_remove:
                self.cancel_task(tid)

            await asyncio.sleep(1)

    def stop(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()


scheduler = LocalScheduler()
