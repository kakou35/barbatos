# =====================================================================
# Script de Lancement 1-Clic BARBATOS — Windows PowerShell
# =====================================================================

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       BARBATOS — AGENT IA LOCAL AUTONOME                " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [1] Terminal Cyberpunk HUD (Console Interactive)" -ForegroundColor White
Write-Host " [2] Dashboard Web HUD (Serveur API & Interface Web)" -ForegroundColor White
Write-Host " [3] Mode Démon avec Surveillance Matérielle" -ForegroundColor White
Write-Host " [4] Lancer le Workflow de Diagnostic Système" -ForegroundColor White
Write-Host " [Q] Quitter" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

$choice = Read-Host "Sélectionnez votre mode (1-4, ou Q)"

switch ($choice) {
    "1" {
        python barbatos_cli.py --mode cli
    }
    "2" {
        Start-Process "http://127.0.0.1:8088"
        python barbatos_cli.py --mode web --port 8088
    }
    "3" {
        python barbatos_cli.py --mode daemon
    }
    "4" {
        python barbatos_cli.py --workflow workflows/system_diagnostic.yaml
    }
    "Q" {
        Exit
    }
    Default {
        python barbatos_cli.py --mode cli
    }
}
