#!/usr/bin/env bash
# =====================================================================
# Script d'Installation Automatisé BARBATOS — Linux / macOS
# =====================================================================

set -e

echo -e "\033[1;36m=====================================================\033[0m"
echo -e "\033[1;36m   INSTALLATION DE L'AGENT IA LOCAL BARBATOS        \033[0m"
echo -e "\033[1;36m=====================================================\033[0m"

# 1. Vérification de Python
echo -e "\n\033[1;33m[1/4] Vérification de Python...\033[0m"
python3 --version || { echo "Python 3 requis."; exit 1; }

# 2. Installation des dépendances
echo -e "\n\033[1;33m[2/4] Installation des dépendances pip...\033[0m"
pip install -r requirements.txt

# 3. Vérification d'Ollama
echo -e "\n\033[1;33m[3/4] Vérification d'Ollama...\033[0m"
if command -v ollama &> /dev/null; then
    echo "Ollama est présent."
    ollama list | grep -q "llama3.1" || ollama pull llama3.1:latest
else
    echo "Ollama non détecté. Installez-le depuis https://ollama.ai"
fi

# 4. Dossiers
mkdir -p data/snapshots data/screenshots

echo -e "\n\033[1;32mInstallation terminée. Lancez : python3 barbatos_cli.py\033[0m"
