"""
Gestionnaire de flux vidéo et de webcam multithreadé pour BARBATOS.
Permet d'extraire des frames en direct et d'enregistrer des instantanés (snapshots).
Fonctionne avec OpenCV et gère élégamment l'absence de caméra physique.
"""

import logging
from pathlib import Path
import threading
import time
from typing import Optional, Tuple, Any
from config.settings import settings

logger = logging.getLogger("Barbatos.Camera")


class CameraManager:
    """Gestionnaire de périphérique webcam avec capture non-bloquante."""

    def __init__(self, camera_index: Optional[int] = None):
        self.camera_index = camera_index if camera_index is not None else settings.vision.camera_index
        self._cap = None
        self._is_open = False
        self._last_frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start_capture(self) -> bool:
        """Initialise et démarre la capture dans un thread dédié."""
        if self._running:
            return True

        try:
            import cv2
            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                logger.warning(f"Impossible d'ouvrir la caméra à l'index {self.camera_index}.")
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.vision.frame_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.vision.frame_height)
            self._is_open = True
            self._running = True

            self._thread = threading.Thread(target=self._capture_worker, daemon=True)
            self._thread.start()
            logger.info("Flux caméra démarré avec succès.")
            return True
        except ImportError:
            logger.info("OpenCV (cv2) n'est pas installé. La caméra fonctionnera en mode simulation.")
            return False
        except Exception as e:
            logger.warning(f"Erreur d'initialisation caméra : {e}")
            return False

    def _capture_worker(self):
        """Lit continuellement les frames pour vider le buffer matériel et garder la plus récente."""
        try:
            import cv2
            while self._running and self._cap and self._cap.isOpened():
                ret, frame = self._cap.read()
                if ret:
                    with self._lock:
                        self._last_frame = frame
                time.sleep(0.03)  # ~30 FPS
        except Exception as e:
            logger.error(f"Erreur dans le thread caméra : {e}")

    def get_latest_frame(self) -> Optional[Any]:
        """Retourne la dernière image capturée."""
        with self._lock:
            return self._last_frame.copy() if self._last_frame is not None else None

    def capture_snapshot(self, output_dir: Optional[str] = None) -> Optional[str]:
        """Capture une image et l'enregistre sur le disque."""
        out_dir = Path(output_dir or settings.vision.snapshot_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"snapshot_{int(time.time())}.jpg"
        target_path = out_dir / filename

        frame = self.get_latest_frame()
        if frame is not None:
            try:
                import cv2
                cv2.imwrite(str(target_path), frame)
                return str(target_path.resolve())
            except Exception as e:
                logger.error(f"Erreur enregistrement image : {e}")

        # Si pas de flux caméra actif, tentative de capture d'écran de repli
        try:
            from system.windows_ops import windows_ops
            result = windows_ops.take_screenshot(output_dir=str(out_dir))
            return result.get("file_path")
        except Exception:
            return None

    def stop(self):
        """Arrête la capture et libère la ressource matérielle."""
        self._running = False
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._is_open = False


camera_manager = CameraManager()
