"""
Interface Terminal HUD Cyberpunk pour BARBATOS.
Construit avec 'rich' pour un affichage interactif moderne en temps réel.
"""

import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box

from config.settings import settings
from core.state import state_manager, AgentState
from core.bus import event_bus, Event
from core.agent import barbatos
from ai.tools_registry import tools_registry
from system.windows_ops import windows_ops

console = Console()

BANNER = """
[bold cyan]  ██████╗  █████╗ ██████╗ ██████╗  █████╗ ████████╗ ██████╗ ███████╗[/bold cyan]
[bold cyan]  ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝[/bold cyan]
[bold cyan]  ██████╔╝███████║██████╔╝██████╔╝███████║   ██║   ██║   ██║███████╗[/bold cyan]
[bold cyan]  ██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══██║   ██║   ██║   ██║╚════██║[/bold cyan]
[bold cyan]  ██████╔╝██║  ██║██║  ██║██████╔╝██║  ██║   ██║   ╚██████╔╝███████║[/bold cyan]
[dim cyan]  Local Autonomous AI Operating System — v1.0.0 — Engine: Ollama / LLaMA 3.1[/dim cyan]
"""


class TerminalHUD:
    """Afficheur interactif dans le terminal."""

    def __init__(self):
        self.logs: list[str] = []
        self._setup_bus()

    def _setup_bus(self):
        async def on_event(event: Event):
            if event.topic.startswith("agent.") or event.topic.startswith("workflow."):
                timestamp = event.timestamp.strftime("%H:%M:%S")
                if event.topic == "agent.thought":
                    self.logs.append(f"[dim cyan]{timestamp}[/dim cyan] [bold purple]THOUGHT :[/bold purple] {event.data.get('thought')}")
                elif event.topic == "agent.tool_called":
                    self.logs.append(f"[dim cyan]{timestamp}[/dim cyan] [bold yellow]ACTION :[/bold yellow] Outil [bold]{event.data.get('tool')}[/bold] invoqué")
                elif event.topic == "agent.final_answer":
                    self.logs.append(f"[dim cyan]{timestamp}[/dim cyan] [bold green]FINAL ANSWER :[/bold green] {event.data.get('answer')[:120]}...")
            if len(self.logs) > 25:
                self.logs.pop(0)

        event_bus.subscribe("*", on_event)

    def print_banner(self):
        console.print(BANNER)

    def print_status(self):
        status = state_manager.get_status_summary()
        hw = windows_ops.get_hardware_metrics()

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Paramètre", style="cyan")
        table.add_column("Valeur", style="bold white")

        table.add_row("État Agent", f"[bold green]{status['state']}[/bold green]")
        table.add_row("Activité", status['activity'])
        table.add_row("Uptime", f"{status['uptime_seconds']} s")
        table.add_row("Tâches Terminées", str(status['tasks_completed']))
        table.add_row("CPU", f"{hw['cpu_percent']} %")
        table.add_row("RAM", f"{hw['ram_percent']} % ({hw['ram_used_gb']} / {hw['ram_total_gb']} Go)")
        if hw.get("battery_percent") is not None:
            table.add_row("Batterie", f"{hw['battery_percent']} % ({'Branche' if hw['battery_plugged'] else 'Batterie'})")

        console.print(Panel(table, title="[bold cyan]SYSTÈME & STATUT ACTUEL[/bold cyan]", border_style="cyan"))

    def print_tools(self):
        tools = tools_registry.list_tools()
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow")
        table.add_column("Nom Outil", style="bold cyan")
        table.add_column("Description", style="white")

        for t in tools:
            table.add_row(t["name"], t["description"])

        console.print(Panel(table, title="[bold yellow]OUTILS SYSTÈME DISPONIBLES[/bold yellow]", border_style="yellow"))

    async def run_interactive_session(self):
        """Boucle de commande interactive en console."""
        self.print_banner()
        self.print_status()

        console.print("[dim white]Tapez votre instruction en langage naturel, ou '/help', '/status', '/tools', '/exit' :[/dim white]\n")

        while True:
            try:
                # Lecture non-bloquante de l'invite
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: console.input("[bold cyan]BARBATOS[/bold cyan] [bold green]❯[/bold green] ")
                )
                cmd = user_input.strip()
                if not cmd:
                    continue

                if cmd.lower() in ["/exit", "/quit"]:
                    console.print("[bold red]Arrêt de BARBATOS... Au revoir.[/bold red]")
                    break
                elif cmd.lower() == "/status":
                    self.print_status()
                    continue
                elif cmd.lower() == "/tools":
                    self.print_tools()
                    continue
                elif cmd.lower() == "/help":
                    console.print(Panel(
                        "Commandes HUD :\n"
                        "  [bold cyan]/status[/bold cyan] : Affiche les métriques matérielles et l'état de l'agent\n"
                        "  [bold cyan]/tools[/bold cyan]  : Liste les outils système disponibles pour le LLM\n"
                        "  [bold cyan]/exit[/bold cyan]   : Quitter l'application\n\n"
                        "Ou entrez simplement n'importe quelle consigne (ex: 'Diagnostique mon PC', 'Prends une capture d'écran', 'Crée un fichier résumé.txt')",
                        title="[bold green]Aide BARBATOS[/bold green]",
                        border_style="green"
                    ))
                    continue

                # Traitement de la commande
                console.print(f"\n[bold yellow]⚡ Analyse et exécution...[/bold yellow]")
                answer = await barbatos.process_command(cmd)
                console.print(Panel(Text(answer, style="bold white"), title="[bold cyan]BARBATOS REPONSE[/bold cyan]", border_style="cyan"))
                console.print()

            except (KeyboardInterrupt, EOFError):
                break


terminal_hud = TerminalHUD()
