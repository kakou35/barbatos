"""
Point d'entrée principal pour BARBATOS — Local Autonomous AI Operating System.
"""

import argparse
import asyncio
import logging
import sys
import uvicorn

from config.settings import settings
from core.agent import barbatos
from ui.terminal_hud import terminal_hud
from automation.workflow_engine import workflow_engine

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Barbatos.Main")


async def run_single_command(command: str):
    """Exécute une instruction unique et quitte."""
    await barbatos.start()
    answer = await barbatos.process_command(command)
    print("\n" + "=" * 50)
    print(f"RÉPONSE BARBATOS :\n{answer}")
    print("=" * 50 + "\n")
    await barbatos.stop()


async def run_workflow_file(workflow_path: str):
    """Charge et exécute un fichier de workflow YAML."""
    await barbatos.start()
    wf = workflow_engine.load_from_yaml(workflow_path)
    result = await workflow_engine.execute_workflow(wf)
    print("\n" + "=" * 50)
    print(f"RÉSULTAT DU WORKFLOW [{wf.name}] :")
    print(f"Statut global : {'SUCCÈS' if result['success'] else 'ÉCHEC'}")
    for s in result["steps"]:
        print(f"  • {s['name']} (ID: {s['step_id']}) -> {'OK' if s['success'] else 'ERREUR'}")
    print("=" * 50 + "\n")
    await barbatos.stop()


def start_web_server(host: str, port: int):
    """Lance le serveur FastAPI / Web HUD."""
    from network.api_server import app
    print(f"\n[HUD WEB] Interface accessible sur : http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")


async def run_interactive(enable_audio: bool, enable_vision: bool):
    """Lance l'interface Terminal HUD avec l'agent actif."""
    await barbatos.start(enable_audio=enable_audio, enable_vision=enable_vision)
    await terminal_hud.run_interactive_session()
    await barbatos.stop()


def main():
    parser = argparse.ArgumentParser(
        description="BARBATOS — Agent IA Local Autonome & Système d'Exploitation Intelligent",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "web", "daemon"],
        default="cli",
        help="Mode d'exécution : 'cli' (Terminal HUD), 'web' (Web HUD), 'daemon' (Agent de fond)"
    )
    parser.add_argument(
        "--cmd",
        type=str,
        default=None,
        help="Exécute une commande directe en langage naturel et quitte."
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Chemin vers un fichier de workflow YAML à exécuter."
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Active l'écoute continue du microphone et le wake word."
    )
    parser.add_argument(
        "--vision",
        action="store_true",
        help="Active le flux et l'analyse vidéo webcam."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.system.web_hud_port,
        help="Port du serveur Web HUD (défaut : 8088)."
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.system.web_hud_host,
        help="Hôte du serveur Web HUD (défaut : 127.0.0.1)."
    )

    args = parser.parse_args()

    # 1. Mode commande directe
    if args.cmd:
        asyncio.run(run_single_command(args.cmd))
        return

    # 2. Mode workflow dédié
    if args.workflow:
        asyncio.run(run_workflow_file(args.workflow))
        return

    # 3. Mode Web uniquement
    if args.mode == "web":
        start_web_server(args.host, args.port)
        return

    # 4. Mode Daemon
    if args.mode == "daemon":
        async def daemon_loop():
            await barbatos.start(enable_audio=args.audio, enable_vision=args.vision)
            print("[DAEMON] BARBATOS est en cours d'exécution en arrière-plan. Ctrl+C pour arrêter.")
            while True:
                await asyncio.sleep(1)
        try:
            asyncio.run(daemon_loop())
        except KeyboardInterrupt:
            print("\n[DAEMON] Arrêt.")
        return

    # 5. Mode CLI par défaut (Terminal HUD)
    asyncio.run(run_interactive(enable_audio=args.audio, enable_vision=args.vision))


if __name__ == "__main__":
    main()
