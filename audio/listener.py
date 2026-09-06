"""
Module d'écoute continue du microphone avec détection VAD et réveil par mot-clé.
Tourne en tâche d'arrière-plan asynchrone non-bloquante.
"""

import asyncio
import logging
import threading
import time
from typing import Optional
from config.settings import settings
from core.bus import event_bus
from core.state import state_manager, AgentState
from audio.stt import local_stt
from audio.wake_word import wake_word_detector

logger = logging.getLogger("Barbatos.Listener")


class AudioListener:
    """Surveille le flux du microphone en continu."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.enabled = settings.audio.enabled

    def start(self):
        """Démarre l'écoute en continu dans un thread dédié."""
        if not self.enabled or self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Module d'écoute audio continue initialisé.")

    def stop(self):
        """Arrête la surveillance du micro."""
        self._running = False

    def _listen_loop(self):
        """Boucle de capture et de surveillance audio."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = settings.audio.energy_threshold
            recognizer.pause_threshold = settings.audio.pause_threshold

            with sr.Microphone() as source:
                logger.info("Calibration du bruit ambiant...")
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                logger.info("Microphone calibré. En attente du mot-clé 'Barbatos'...")

                while self._running:
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        text = local_stt.transcribe_audio_data(audio)
                        if text:
                            logger.info(f"Son détecté : '{text}'")
                            if wake_word_detector.is_wake_word_present(text):
                                clean_command = wake_word_detector.strip_wake_word(text)
                                logger.info(f"Wake word détecté ! Commande : '{clean_command}'")

                                # Envoi sur le bus d'événements asynchrone
                                asyncio.run(event_bus.publish(
                                    "audio.command_received",
                                    {"raw_text": text, "command": clean_command},
                                    sender="audio_listener"
                                ))
                    except Exception:
                        continue

        except (ImportError, OSError) as e:
            logger.warning(f"Microphone ou bibliothèque audio non disponible ({e}). Mode vocal passif activé.")
            self._running = False


audio_listener = AudioListener()
