"""
Module de gestion de configuration pour Barbatos.
Charge la configuration depuis YAML et les variables d'environnement avec validation Pydantic.
"""

import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    name: str = "BARBATOS"
    version: str = "1.0.0"
    log_level: str = "INFO"
    locale: str = "fr_FR"
    auto_start_web_hud: bool = True
    web_hud_port: int = 8088
    web_hud_host: str = "127.0.0.1"


class AIConfig(BaseModel):
    provider: str = "ollama"
    ollama_endpoint: str = "http://localhost:11434"
    model: str = "llama3.1:latest"
    vision_model: str = "llama3.2-vision:latest"
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout_seconds: int = 60
    react_max_steps: int = 8


class MemoryConfig(BaseModel):
    sqlite_path: str = "data/barbatos_memory.db"
    short_term_window: int = 15
    long_term_enabled: bool = True


class AudioConfig(BaseModel):
    enabled: bool = True
    wake_word: str = "barbatos"
    wake_word_aliases: List[str] = Field(default_factory=lambda: ["barbatos", "hey barbatos", "assistant"])
    energy_threshold: int = 400
    pause_threshold: float = 1.2
    tts_engine: str = "native"
    voice_speed: int = 165
    voice_volume: float = 1.0


class VisionConfig(BaseModel):
    enabled: bool = True
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    detection_confidence: float = 0.5
    snapshot_dir: str = "data/snapshots"


class SecurityConfig(BaseModel):
    allow_arbitrary_commands: bool = True
    dangerous_commands_blacklist: List[str] = Field(
        default_factory=lambda: [
            "format ",
            "rmdir /s /q c:\\",
            "rm -rf /",
            "del /f /s /q c:\\windows",
        ]
    )
    require_confirmation_for_destructive: bool = True


class NetworkConfig(BaseModel):
    api_enabled: bool = True
    api_secret_key: str = "barbatos-local-secret-token"
    ssh_default_port: int = 22


class Settings(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Settings":
        """Charge la configuration depuis un fichier YAML ou utilise les valeurs par défaut."""
        if config_path is None:
            base_dir = Path(__file__).resolve().parent
            config_path = str(base_dir / "default_config.yaml")

        path = Path(config_path)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return cls(**data)
            except Exception as e:
                print(f"[WARN] Erreur chargement config {config_path}: {e}, utilisation des valeurs par défaut.")
                return cls()
        return cls()


# Instance globale chargée
settings = Settings.load()
