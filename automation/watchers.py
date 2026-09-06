"""
Surveillants d'événements système en temps réel pour BARBATOS.
Surveillance de répertoires (Watchdog) et sondes d'alertes matérielles (CPU, RAM).
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable
import psutil
from core.bus import event_bus

logger = logging.getLogger("Barbatos.Watchers")


class HardwareThresholdWatcher:
    """Surveille en continu l'utilisation CPU et RAM et émet des alertes si les seuils sont franchis."""

    def __init__(self, cpu_threshold: float = 90.0, ram_threshold: float = 90.0):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=1.0)
                ram = psutil.virtual_memory().percent

                if cpu >= self.cpu_threshold:
                    await event_bus.publish(
                        "system.alert.high_cpu",
                        {"cpu_percent": cpu, "threshold": self.cpu_threshold},
                        sender="hardware_watcher"
                    )

                if ram >= self.ram_threshold:
                    await event_bus.publish(
                        "system.alert.high_ram",
                        {"ram_percent": ram, "threshold": self.ram_threshold},
                        sender="hardware_watcher"
                    )

            except Exception as e:
                logger.error(f"Erreur surveillance hardware : {e}")

            await asyncio.sleep(5)

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()


class FileSystemWatcher:
    """Surveille un répertoire pour détecter les modifications ou ajouts de fichiers."""

    def __init__(self, directory: str):
        self.directory = str(Path(directory).resolve())
        self._observer = None

    def start(self):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class Handler(FileSystemEventHandler):
                def on_created(self, event):
                    if not event.is_directory:
                        asyncio.run(event_bus.publish("file.created", {"path": event.src_path}, sender="file_watcher"))

                def on_modified(self, event):
                    if not event.is_directory:
                        asyncio.run(event_bus.publish("file.modified", {"path": event.src_path}, sender="file_watcher"))

            self._observer = Observer()
            self._observer.schedule(Handler(), self.directory, recursive=True)
            self._observer.start()
            logger.info(f"Surveillance de répertoire active sur : {self.directory}")
        except Exception as e:
            logger.warning(f"Impossible d'activer watchdog sur {self.directory}: {e}")

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()


hardware_watcher = HardwareThresholdWatcher()
