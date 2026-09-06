# =====================================================================
# Script d'Installation Automatisé BARBATOS — Windows PowerShell
# =====================================================================

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   INSTALLATION DE L'AGENT IA LOCAL BARBATOS        " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Vérification de Python
Write-Host "`n[1/4] Vérification de l'environnement Python..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVersion = python --version
    Write-Host "  -> Python détecté : $pyVersion" -ForegroundColor Green
} else {
    Write-Host "  [ERREUR] Python n'est pas installé ou non présent dans le PATH." -ForegroundColor Red
    Exit 1
}

# 2. Installation des dépendances pip
Write-Host "`n[2/4] Installation des dépendances Python..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "  -> Dépendances installées avec succès." -ForegroundColor Green
} else {
    Write-Host "  [AVERTISSEMENT] Certaines dépendances optionnelles n'ont pas pu s'installer." -ForegroundColor Yellow
}

# 3. Vérification d'Ollama
Write-Host "`n[3/4] Vérification du serveur local Ollama..." -ForegroundColor Yellow
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    $ollamaVer = ollama --version
    Write-Host "  -> Ollama détecté : $ollamaVer" -ForegroundColor Green
    
    Write-Host "  -> Vérification du modèle llama3.1..." -ForegroundColor Yellow
    $models = ollama list
    if ($models -match "llama3.1") {
        Write-Host "  -> Modèle llama3.1 déjà installé et prêt !" -ForegroundColor Green
    } else {
        Write-Host "  -> Téléchargement du modèle llama3.1 (cela peut prendre quelques minutes)..." -ForegroundColor Cyan
        ollama pull llama3.1:latest
    }
} else {
    Write-Host "  [ATTENTION] Ollama n'est pas détecté. Rendez-vous sur https://ollama.ai pour l'installer." -ForegroundColor Yellow
}

# 4. Création des dossiers de données
Write-Host "`n[4/4] Préparation des répertoires de travail..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\snapshots" | Out-Null
New-Item -ItemType Directory -Force -Path "data\screenshots" | Out-Null
Write-Host "  -> Dossiers data/ préparés." -ForegroundColor Green

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "   INSTALLATION TERMINÉE AVEC SUCCÈS !              " -ForegroundColor Green
Write-Host "   Pour lancer l'agent :" -ForegroundColor White
Write-Host "     python barbatos_cli.py                         " -ForegroundColor Cyan
Write-Host "     ou utilisez .\scripts\run_barbatos.ps1         " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
