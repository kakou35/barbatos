"""
Module de Sécurité et Interface de Contrôle (Manager Surface / Human-in-the-Loop).
Implémente la politique de sécurité de l'agent :
- Lecture et extraction : AUTORISÉES AUTOMATIQUEMENT
- Navigation autonome et requêtes web externes : SOUMISES À VALIDATION D'UN CLIC
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from enum import Enum
from typing import List
from tech_scout.analyzer import DiscoveredTool

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


class PolicyAction(Enum):
    ALLOW = "ALLOW"
    ASK_USER = "ASK_USER"
    DENY = "DENY"


class SecurityPolicy:
    """Définit les règles d'accès et d'exécution de l'agent autonome."""
    
    # Lecture et extraction de contenu local/source
    READ_AND_EXTRACT = PolicyAction.ALLOW
    
    # Navigation web externe et requêtes de recherche
    AUTONOMOUS_WEB_NAVIGATION = PolicyAction.ASK_USER


def display_manager_surface(tools: List[DiscoveredTool], source_url: str) -> None:
    """
    Affiche le tableau de bord de supervision dans la 'Manager Surface'.
    Présente un récapitulatif clair et visuel pour l'approbation humaine.
    """
    if HAS_RICH:
        title_text = Text("🛡️ ANTIGRAVITY MANAGER SURFACE — HUMAN-IN-THE-LOOP", style="bold cyan")
        
        info_text = (
            f"[bold white]Source analysée :[/bold white] [dim]{source_url}[/dim]\n"
            f"[bold white]Politique de Sécurité :[/bold white] "
            f"[green]Lecture : AUTO-ALLOW[/green] | [yellow]Browser Sub-agent : REQUIRE-REVIEW[/yellow]\n"
            f"[bold white]Outils identifiés :[/bold white] [bold green]{len(tools)} outil(s)[/bold green]"
        )
        
        table = Table(title="Outils détectés à enrichir par navigation autonome", show_lines=True)
        table.add_column("#", style="dim", width=4, justify="center")
        table.add_column("Nom de l'Outil", style="bold green", min_width=15)
        table.add_column("Catégorie Estimée", style="magenta", min_width=18)
        table.add_column("Action Prévue", style="yellow", min_width=25)

        for i, tool in enumerate(tools, start=1):
            table.add_row(
                str(i),
                tool.name,
                tool.category,
                f"🔍 Recherche Google & extraction URL officielle"
            )

        console.print(Panel(info_text, title=title_text, border_style="cyan"))
        console.print(table)
    else:
        # Fallback console standard si 'rich' n'est pas encore installé
        print("\n" + "=" * 70)
        print("🛡️  ANTIGRAVITY MANAGER SURFACE — HUMAN-IN-THE-LOOP")
        print("=" * 70)
        print(f"Source analysée        : {source_url}")
        print("Politique de Sécurité  : Lecture [AUTO-ALLOW] | Navigation [REQUIRE-REVIEW]")
        print(f"Outils identifiés      : {len(tools)} outil(s)")
        print("-" * 70)
        print(f"{'#':<4} {'Nom de l Outil':<20} {'Catégorie':<20} {'Action Prévue'}")
        print("-" * 70)
        for i, tool in enumerate(tools, start=1):
            print(f"{i:<4} {tool.name:<20} {tool.category:<20} Recherche Google / Site Officiel")
        print("=" * 70)


def request_manager_approval(tools: List[DiscoveredTool], source_url: str, auto_approve: bool = False) -> List[DiscoveredTool]:
    """
    Sollicite l'accord de l'opérateur humain avant d'engager le sous-agent navigateur.
    Un simple appui sur la touche [Entrée] ou 'O' permet de valider d'un clic.
    """
    if not tools:
        print("[Manager Surface] Aucun outil détecté à soumettre à validation.")
        return []

    # Affichage de la surface de gestion
    display_manager_surface(tools, source_url)

    if auto_approve:
        if HAS_RICH:
            console.print("[bold green]✔ Auto-approbation activée (--auto-approve). Démarrage de la navigation...[/bold green]\n")
        else:
            print("✔ Auto-approbation activée. Démarrage de la navigation...\n")
        return tools

    # Point d'interaction Human-in-the-Loop
    prompt_msg = (
        "\n👉 Validez-vous le lancement du Browser Sub-agent pour ces outils ? "
        "[O/n] (Entrée = Valider d'un clic) : "
    )
    
    try:
        user_input = input(prompt_msg).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nOpération interrompue par l'utilisateur.")
        sys.exit(0)

    if user_input in ["", "o", "oui", "y", "yes"]:
        if HAS_RICH:
            console.print("[bold green]✔ Autorisation accordée par le Manager. Lancement de la navigation autonome ![/bold green]\n")
        else:
            print("✔ Autorisation accordée par le Manager. Lancement de la navigation autonome !\n")
        return tools
    else:
        print("\n❌ Navigation autonome annulée par le superviseur.")
        print("💡 Vous pouvez relancer le script avec une autre URL.")
        sys.exit(0)
