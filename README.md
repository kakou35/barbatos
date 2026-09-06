[README.md](https://github.com/user-attachments/files/31889487/README.md)
# 🤖 BARBATOS — Local Autonomous AI Operating System

```text
  ██████╗  █████╗ ██████╗ ██████╗  █████╗ ████████╗ ██████╗ ███████╗
  ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝
  ██████╔╝███████║██████╔╝██████╔╝███████║   ██║   ██║   ██║███████╗
  ██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══██║   ██║   ██║   ██║╚════██║
  ██████╔╝██║  ██║██║  ██║██████╔╝██║  ██║   ██║   ╚██████╔╝███████║
  Local Autonomous AI Operating System — v1.0.0 — Engine: Ollama / LLaMA 3.1
```

**BARBATOS** est un système d'exploitation IA personnel, modulaire et 100% autonome, conçu pour fonctionner en local (Windows en priorité, compatible Linux). Il transforme un LLM local (Ollama / LLaMA 3.1) en un véritable **cerveau orchestrateur** capable d'agir sur le système, de voir via la caméra, d'entendre via le micro et d'automatiser des flux de tâches complexes.

---

## ⚡ Capacités Clés

- 🧠 **Cerveau ReAct Autonome** : Boucle de décision *(Penser ➔ Agir ➔ Observer ➔ Corriger ➔ Conclure)*.
- 💻 **Contrôle Système Avancé** :
  - Exécution sécurisée PowerShell / Bash avec liste noire anti-destructrice.
  - Surveillance et pilotage des processus et applications (`psutil`).
  - Gestion de fichiers (recherche récursive, lecture/écriture, métadonnées).
  - Intégration native Windows (Toast notifications, capture d'écran, presse-papier, audio).
- 🎤 **Module Vocal Local (Offline)** :
  - Détection du Wake Word (*"Barbatos"*, *"Hey Barbatos"*).
  - Synthèse vocale locale TTS (SAPI5 natif / `pyttsx3`) sans latence internet.
  - Écoute continue en arrière-plan non-bloquante.
- 👁 **Vision IA Intégrée** :
  - Flux webcam OpenCV multithreadé.
  - Détection de visages et présence humaine.
  - Détection et tracking géométrique d'objets (`CentroidTracker`).
  - Capture d'instantanés et de captures d'écran.
- 🌐 **Réseau & Partages** :
  - Client SSH distant pour piloter des machines et serveurs Linux.
  - Montage et gestion des partages réseau SMB / UNC (`net use`).
  - API locale FastAPI (REST + WebSockets).
- 🧩 **Automatisation Avancée** :
  - Moteur de workflows déclaratifs en YAML (séquences avec transmission de variables).
  - Scheduler de tâches récurrentes (Cron local).
  - Surveillants de seuils de santé matérielle (alertes CPU/RAM > 90%).
- 🖥 **Double Interface Utilisateur (HUD)** :
  - **Terminal HUD Cyberpunk** : Console interactive en temps réel avec `rich`.
  - **Web HUD Dashboard** : Interface Web futuriste néon avec jauges, télémétrie et flux d'événements WebSockets.

---

## 🗂️ Structure du Projet

```text
barbatos/
├── config/
│   ├── settings.py             # Configuration Pydantic validée
│   ├── default_config.yaml     # Paramètres par défaut (Ollama, seuils, ports)
│   └── prompts.py              # Prompts ReAct & directives tactiques
├── core/
│   ├── bus.py                  # EventBus asynchrone (Pub/Sub inter-modules)
│   ├── state.py                # Machine à états (IDLE, THINKING, EXECUTING...)
│   ├── memory.py               # Mémoire court terme + Long terme (SQLite)
│   └── agent.py                # Orchestrateur central BarbatosAgent
├── ai/
│   ├── llm_client.py           # Client Ollama local asynchrone
│   ├── brain.py                # Boucle décisionnelle ReAct
│   ├── planner.py              # Décomposeur de tâches multi-étapes
│   └── tools_registry.py       # Registre dynamique des outils système
├── system/
│   ├── shell.py                # Exécution sécurisée PowerShell / Bash
│   ├── apps.py                 # Gestionnaire de processus & applications
│   ├── files.py                # Opérations sur fichiers & dossiers
│   └── windows_ops.py          # Notifications Toast, Volume, Screenshots, RAM/CPU
├── audio/
│   ├── listener.py             # Écoute micro continue & VAD
│   ├── wake_word.py            # Détecteur de mot-clé d'activation
│   ├── stt.py                  # Transcription vocale locale
│   └── tts.py                  # Synthèse vocale offline (pyttsx3)
├── vision/
│   ├── camera.py               # Gestionnaire de flux webcam OpenCV
│   ├── detector.py             # Détection d'objets
│   ├── face.py                 # Détection de visages & présence
│   ├── tracker.py              # Suivi d'objets temps réel (Centroid)
│   └── scene_analyzer.py       # Analyse de scène & d'écran
├── network/
│   ├── ssh_client.py           # Client SSH (Paramiko)
│   ├── smb_client.py           # Partages Windows SMB / UNC
│   └── api_server.py           # Serveur FastAPI + WebSockets pour le HUD
├── automation/
│   ├── workflow_engine.py      # Moteur de workflows DAG (YAML)
│   ├── scheduler.py            # Planificateur de tâches périodiques
│   ├── watchers.py             # Surveillance fichiers & alertes CPU/RAM
│   └── macros.py               # Macros d'actions rapides
├── ui/
│   ├── terminal_hud.py         # Interface Terminal CLI Cyberpunk
│   └── static/                 # Dashboard Web HUD
│       ├── index.html
│       ├── style.css
│       └── app.js
├── workflows/                  # Exemples de workflows YAML
│   ├── system_diagnostic.yaml
│   └── clean_temp_files.yaml
├── scripts/
│   ├── install.ps1             # Installation Windows 1-clic
│   ├── install.sh              # Installation Linux
│   ├── run_barbatos.ps1        # Lancement rapide Windows
│   └── setup_ollama.ps1        # Configuration des modèles Ollama
├── tests/                      # Suite de tests unitaires et d'intégration
│   ├── test_eventbus.py
│   ├── test_system.py
│   ├── test_workflow.py
│   └── test_brain.py
├── barbatos_cli.py             # Point d'entrée exécutable principal
└── requirements.txt            # Dépendances Python
```

---

## 🚀 Installation Rapide

### Sous Windows (PowerShell) :

```powershell
# 1. Installer automatiquement l'environnement et les modèles
.\scripts\install.ps1
```

Ou manuellement :
```bash
pip install -r requirements.txt
```

---

## 🕹️ Modes d'Utilisation

### 1. Terminal Cyberpunk HUD (Mode Recommandé)
Lance une interface console futuriste avec télémétrie temps réel et invite de commande en langage naturel :
```bash
python barbatos_cli.py
# ou
.\scripts\run_barbatos.ps1
```

Commandes internes disponibles dans le Terminal HUD :
- `/status` : Affiche les métriques matérielles et l'état courant.
- `/tools` : Liste tous les outils système accessibles à l'agent.
- `/help` : Affiche l'aide.
- `/exit` : Arrête l'agent proprement.

---

### 2. Dashboard Web HUD (Interface Graphique)
Démarre le serveur FastAPI et l'interface WebSockets :
```bash
python barbatos_cli.py --mode web --port 8088
```
Puis ouvrez votre navigateur sur [http://127.0.0.1:8088](http://127.0.0.1:8088).

---

### 3. Exécution d'une Commande Directe
Pour exécuter une requête ponctuelle sans ouvrir d'interface :
```bash
python barbatos_cli.py --cmd "Donne-moi l'état de la mémoire RAM de mon PC et dis-moi si tout va bien."
```

---

### 4. Exécution d'un Workflow YAML
```bash
python barbatos_cli.py --workflow workflows/system_diagnostic.yaml
```

---

### 5. Mode Démon en Tâche de Fond (avec Audio et Vision)
```bash
python barbatos_cli.py --mode daemon --audio --vision
```

---

## ⚙️ Configuration du LLM Local (`config/default_config.yaml`)

BARBATOS est configuré par défaut pour utiliser le serveur local **Ollama** :
```yaml
ai:
  provider: "ollama"
  ollama_endpoint: "http://localhost:11434"
  model: "llama3.1:latest"
  temperature: 0.2
  react_max_steps: 8
```

Pour vérifier qu'Ollama fonctionne :
```bash
ollama list
```

---

## 🧪 Lancer la Suite de Tests

```bash
python -m tests.test_eventbus
python -m tests.test_system
python -m tests.test_workflow
python -m tests.test_brain
```

---

## 🛡️ Sécurité & Garde-Fous

BARBATOS intègre un module de filtrage strict (`SafeShellExecutor`) empêchant toute exécution de commandes destructrices répertoriées dans la liste noire (`rm -rf /`, `format`, suppressions globales du disque).
