"""
Moteur de synthèse vocale (TTS) 100% local et offline pour BARBATOS.
Utilise pyttsx3 (SAPI5 sous Windows, nsss sous macOS, espeak sous Linux).
Exécution asynchrone non-bloquante via thread dédié.
"""

import asyncio
import logging
import queue
import threading
from typing import Optional
import pyttsx3
from config.settings import settings

logger = logging.getLogger("Barbatos.TTS")


class LocalTTS:
    """Moteur de synthèse vocale offline."""

    def __init__(self):
        self._queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self.enabled = settings.audio.enabled
        self._init_worker()

    def _init_worker(self):
        """Démarre le thread de synthèse vocale."""
        if not self.enabled:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._run_tts_loop, daemon=True)
        self._worker_thread.start()

    def _run_tts_loop(self):
        """Boucle de travail du thread TTS."""
        try:
            engine = pyttsx3.init()
            # Configuration de la vitesse et du volume
            engine.setProperty("rate", settings.audio.voice_speed)
            engine.setProperty("volume", settings.audio.voice_volume)

            # Sélection d'une voix française si disponible
            voices = engine.getProperty("voices")
            for v in voices:
                if "french" in v.name.lower() or "fr" in v.id.lower() or "hortense" in v.name.lower() or "paul" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break

            while self._running:
                try:
                    text = self._queue.get(timeout=0.5)
                    if text is None:
                        break
                    engine.say(text)
                    engine.runAndWait()
                    self._queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Erreur synthèse vocale : {e}")

        except Exception as e:
            logger.warning(f"Impossible d'initialiser pyttsx3 ({e}). TTS désactivé.")
            self.enabled = False

    def speak(self, text: str):
        """Envoie du texte à lire dans la file TTS (non-bloquant)."""
        if not self.enabled or not text:
            return
        # Nettoyage des balises Markdown ou JSON pour une diction propre
        clean_text = text.replace("*", "").replace("`", "").replace("#", "")
        self._queue.put(clean_text)

    async def speak_async(self, text: str):
        """Version coroutine pratique pour l'agent."""
        self.speak(text)

    def stop(self):
        self._running = False
        self._queue.put(None)


tts = LocalTTS()
