"""
Reconnaissance et identification faciale locale pour BARBATOS.
Détecte la présence de l'utilisateur devant l'écran / la webcam.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Barbatos.FaceRecognition")


class FaceSystem:
    """Gestionnaire de détection faciale et de présence utilisateur."""

    def __init__(self):
        self._cascade = None
        self._init_detector()

    def _init_detector(self):
        try:
            import cv2
            self._cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        except Exception as e:
            logger.debug(f"Initialisation visage impossible : {e}")

    def detect_faces(self, frame) -> List[Dict[str, Any]]:
        """Retourne les coordonnées des visages détectés dans l'image."""
        if frame is None or not self._cascade:
            return []

        try:
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(35, 35))

            return [
                {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "center": (int(x + w / 2), int(y + h / 2))
                }
                for (x, y, w, h) in faces
            ]
        except Exception as e:
            logger.error(f"Erreur détection visage : {e}")
            return []

    def is_user_present(self, frame) -> bool:
        """Indique si un utilisateur est visible face à la caméra."""
        return len(self.detect_faces(frame)) > 0


face_system = FaceSystem()
