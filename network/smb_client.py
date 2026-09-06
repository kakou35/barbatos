"""
Gestionnaire de partages réseau SMB / Windows Shares pour BARBATOS.
Permet la connexion, la copie de fichiers et le montage de partages réseau UNC.
"""

import os
import subprocess
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional


class SMBManager:
    """Gestion des lecteurs réseau et partages SMB."""

    @staticmethod
    def mount_share(share_path: str, drive_letter: str = "Z:", username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Monte un partage réseau sur une lettre de lecteur sous Windows (ex: 'net use Z: \\server\\share')."""
        if os.name != 'nt':
            return {"success": False, "error": "Montage natif 'net use' disponible sous Windows uniquement."}

        cmd = ["net", "use", drive_letter, share_path]
        if password and username:
            cmd.extend([password, f"/USER:{username}"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return {
                "success": res.returncode == 0,
                "message": res.stdout.strip() if res.returncode == 0 else res.stderr.strip(),
                "drive": drive_letter,
                "share": share_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def unmount_share(drive_letter: str = "Z:") -> Dict[str, Any]:
        """Déconnecte un lecteur réseau monté."""
        if os.name != 'nt':
            return {"success": False, "error": "Non supporté hors Windows."}

        try:
            res = subprocess.run(["net", "use", drive_letter, "/DELETE", "/YES"], capture_output=True, text=True, timeout=10)
            return {
                "success": res.returncode == 0,
                "message": res.stdout.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_share_files(share_path: str) -> List[str]:
        """Liste les fichiers d'un chemin UNC accessible."""
        p = Path(share_path)
        if not p.exists():
            return []
        try:
            return [str(item.name) for item in p.iterdir()]
        except Exception:
            return []


smb_manager = SMBManager()
