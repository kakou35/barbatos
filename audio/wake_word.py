"""
Détecteur de mot d'activation (Wake Word) local pour BARBATOS.
Identifie les mots clés 'Barbatos', 'Hey Barbatos', etc.
"""

from typing import List
from config.settings import settings


class WakeWordDetector:
    """Analyse les segments textuels ou phonétiques pour déclencher l'écoute active."""

    def __init__(self, wake_words: List[str] = None):
        self.wake_words = [w.lower().strip() for w in (wake_words or settings.audio.wake_word_aliases)]

    def is_wake_word_present(self, text: str) -> bool:
        """Vérifie si l'une des variantes du mot-clé est présente dans le texte transcrit."""
        if not text:
            return False
        clean = text.lower().strip()
        for word in self.wake_words:
            if word in clean:
                return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """Retire le mot-clé de la commande pour ne conserver que l'instruction."""
        clean = text.lower().strip()
        for word in self.wake_words:
            if clean.startswith(word):
                return clean[len(word):].strip(" ,:.-!?")
        return clean


wake_word_detector = WakeWordDetector()
