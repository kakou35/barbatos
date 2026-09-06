"""
Client LLM local asynchrone pour BARBATOS.
Supporte nativement Ollama (/api/chat, /api/generate) avec gestion du streaming,
détection de connectivité et configuration des hyperparamètres.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from config.settings import settings

logger = logging.getLogger("Barbatos.LLMClient")


class OllamaClient:
    """Interface asynchrone avec le démon Ollama local."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        self.endpoint = (endpoint or settings.ai.ollama_endpoint).rstrip("/")
        self.model = model or settings.ai.model
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds or settings.ai.timeout_seconds)

    async def is_available(self) -> bool:
        """Vérifie si le serveur Ollama est démarré et répond."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                async with session.get(f"{self.endpoint}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Récupère la liste des modèles installés localement."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.endpoint}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Impossible de lister les modèles Ollama : {e}")
        return []

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        format_json: bool = False,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Envoie un appel de chat standard à Ollama et retourne la réponse texte complète."""
        url = f"{self.endpoint}/api/chat"

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.ai.temperature,
                "num_predict": settings.ai.max_tokens,
            }
        }

        if format_json:
            payload["format"] = "json"

        timeout = aiohttp.ClientTimeout(total=settings.ai.timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content", "").strip()
                    else:
                        text_err = await resp.text()
                        raise RuntimeError(f"Ollama HTTP {resp.status} : {text_err}")
        except Exception as e:
            e_msg = str(e) if str(e) else "Delai d'attente depasse (Timeout)"
            err_detail = f"{type(e).__name__}: {e_msg}"
            logger.error(f"Erreur requête Ollama : {err_detail}")
            raise RuntimeError(err_detail)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Génère la réponse Ollama en flux continu (streaming)."""
        url = f"{self.endpoint}/api/chat"

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": settings.ai.temperature,
                "num_predict": settings.ai.max_tokens,
            }
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    yield f"[Erreur Ollama HTTP {resp.status}]"
                    return

                async for line in resp.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue


# Instance par défaut
llm_client = OllamaClient()
