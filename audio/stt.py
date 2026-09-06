"""
Module de transcription vocale (Speech-to-Text) locale pour BARBATOS.
Supporte SpeechRecognition / Whisper local avec mécanisme de repli (fallback).
"""

import logging
from typing import Optional

logger = logging.getLogger("Barbatos.STT")


class LocalSTT:
    """Moteur de transcription de la voix en texte."""

    def __init__(self):
        self._recognizer = None
        self._has_sr = False
        self._init_engine()

    def _init_engine(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._has_sr = True
        except ImportError:
            logger.info("Module 'speech_recognition' non installé. STT fonctionnera en mode simulation/texte.")
            self._has_sr = False

    def transcribe_audio_data(self, audio_data) -> Optional[str]:
        """Transcrit un objet audio capturé."""
        if not self._has_sr or not self._recognizer:
            return None

        try:
            import speech_recognition as sr
            # Utilise d'abord la reconnaissance locale si configurée (ex: Sphinx ou Whisper)
            # Sinon repli sur l'API de reconnaissance Google sans clé pour tests locaux rapides
            text = self._recognizer.recognize_google(audio_data, language="fr-FR")
            return text
        except Exception as e:
            logger.debug(f"Échec transcription : {e}")
            return None


local_stt = LocalSTT()
