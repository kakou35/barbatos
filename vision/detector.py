"""
Détection d'objets en temps réel pour BARBATOS.
Utilise OpenCV DNN / Haar ou heuristique visuelle pour détecter personnes et objets.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Barbatos.VisionDetector")


class ObjectDetector:
    """Détecteur d'objets sur les images capturées."""

    def __init__(self):
        self._cascade_face = None
        self._cascade_upperbody = None
        self._init_models()

    def _init_models(self):
        try:
            import cv2
            # Chargement des cascades OpenCV standard pré-intégrées
            face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            upper_path = cv2.data.haarcascades + "haarcascade_upperbody.xml"
            self._cascade_face = cv2.CascadeClassifier(face_path)
            self._cascade_upperbody = cv2.CascadeClassifier(upper_path)
        except Exception as e:
            logger.debug(f"Impossible de charger les cascades de détection : {e}")

    def detect_objects_in_frame(self, frame) -> List[Dict[str, Any]]:
        """Détecte les entités présentes dans une frame (visage, personne, mouvement)."""
        if frame is None:
            return []

        results = []
        try:
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Détection de visages
            if self._cascade_face:
                faces = self._cascade_face.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    results.append({
                        "label": "person_face",
                        "confidence": 0.92,
                        "box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                    })

            # Détection de silhouette / buste
            if self._cascade_upperbody:
                bodies = self._cascade_upperbody.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(50, 50))
                for (x, y, w, h) in bodies:
                    results.append({
                        "label": "person_body",
                        "confidence": 0.85,
                        "box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                    })

        except Exception as e:
            logger.error(f"Erreur détection objets : {e}")

        return results


object_detector = ObjectDetector()
