# =====================================================================
# Configuration et Téléchargement des Modèles Ollama pour BARBATOS
# =====================================================================

Write-Host "Vérification de la disponibilité du serveur Ollama..." -ForegroundColor Cyan

try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "Serveur Ollama actif !" -ForegroundColor Green
} catch {
    Write-Host "Le serveur Ollama ne répond pas sur le port 11434." -ForegroundColor Yellow
    Write-Host "Tentative de démarrage en arrière-plan..." -ForegroundColor Cyan
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

Write-Host "Téléchargement du modèle recommandé : llama3.1:latest..." -ForegroundColor Cyan
ollama pull llama3.1:latest

Write-Host "`nModèle prêt pour BARBATOS !" -ForegroundColor Green
