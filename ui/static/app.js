// =====================================================================
// BARBATOS Web HUD — Client Frontend JavaScript (WebSockets & REST)
// =====================================================================

let ws = null;
const terminalFeed = document.getElementById("terminal-feed");
const agentStateEl = document.getElementById("agent-state");
const statusRing = document.getElementById("status-ring");
const uptimeVal = document.getElementById("uptime-val");
const cpuPercent = document.getElementById("cpu-percent");
const cpuBar = document.getElementById("cpu-bar");
const ramPercent = document.getElementById("ram-percent");
const ramBar = document.getElementById("ram-bar");
const ramDetail = document.getElementById("ram-detail");
const tasksCount = document.getElementById("tasks-count");
const batteryStatus = document.getElementById("battery-status");
const toolsList = document.getElementById("tools-list");

// Connexion WebSocket temps réel
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    appendLog("system", "[NETWORK] Liaison neuronale établie avec le noyau BARBATOS.");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleIncomingMessage(data);
    } catch (e) {
      console.error("Erreur parsing WS message :", e);
    }
  };

  ws.onclose = () => {
    appendLog("system", "[NETWORK] Liaison perdue. Reconnexion automatique dans 3s...");
    setTimeout(connectWebSocket, 3000);
  };
}

function handleIncomingMessage(msg) {
  if (msg.type === "status_init") {
    updateStatus(msg.status);
    if (msg.hardware) updateHardware(msg.hardware);
    return;
  }

  if (msg.type === "event") {
    const topic = msg.topic;
    const data = msg.data || {};

    if (topic === "agent.state_changed") {
      setAgentState(data.state, data.activity);
    } else if (topic === "agent.thought") {
      appendLog("thought", `💭 PENSÉE (Étape ${data.step}) : ${data.thought}`);
    } else if (topic === "agent.tool_called") {
      appendLog("action", `⚙️ ACTION : Invoque l'outil [${data.tool}] avec ${JSON.stringify(data.input || {})}`);
    } else if (topic === "agent.tool_result") {
      const resStr = typeof data.result === "object" ? JSON.stringify(data.result) : data.result;
      appendLog("system", `↳ RÉSULTAT [${data.tool}] : ${resStr.substring(0, 180)}`);
    } else if (topic === "agent.final_answer") {
      appendLog("answer", `✅ BARBATOS : ${data.answer}`);
    } else if (topic === "workflow.started") {
      appendLog("action", `🚀 WORKFLOW DÉMARRÉ : ${data.name}`);
    } else if (topic === "workflow.completed") {
      appendLog("system", `🏁 WORKFLOW TERMINÉ : ${data.name} (Succès: ${data.success})`);
    }
  }
}

function setAgentState(state, activity) {
  agentStateEl.textContent = state;
  statusRing.className = "status-ring " + state.toLowerCase();
}

function updateStatus(status) {
  if (!status) return;
  setAgentState(status.state, status.activity);
  uptimeVal.textContent = Math.round(status.uptime_seconds) + "s";
  tasksCount.textContent = status.tasks_completed;
}

function updateHardware(hw) {
  if (!hw) return;
  cpuPercent.textContent = `${hw.cpu_percent}%`;
  cpuBar.style.width = `${hw.cpu_percent}%`;

  ramPercent.textContent = `${hw.ram_percent}%`;
  ramBar.style.width = `${hw.ram_percent}%`;
  ramDetail.textContent = `${hw.ram_used_gb} / ${hw.ram_total_gb} Go`;

  if (hw.battery_percent !== null && hw.battery_percent !== undefined) {
    batteryStatus.textContent = `${hw.battery_percent}% (${hw.battery_plugged ? 'Secteur' : 'Batterie'})`;
  }
}

function appendLog(type, text) {
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.textContent = text;
  terminalFeed.appendChild(line);
  terminalFeed.scrollTop = terminalFeed.scrollHeight;
}

// Envoi de commande
function sendCommand(e) {
  if (e) e.preventDefault();
  const input = document.getElementById("user-input");
  const text = input.value.trim();
  if (!text) return;

  appendLog("user", `❯ ${text}`);
  input.value = "";

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "user_command", text: text }));
  } else {
    // Fallback REST
    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    })
    .then(r => r.json())
    .then(data => {
      appendLog("answer", `✅ BARBATOS : ${data.answer}`);
    })
    .catch(err => {
      appendLog("system", `[ERREUR] Requête échouée : ${err}`);
    });
  }
}

function executeQuick(prompt) {
  const input = document.getElementById("user-input");
  input.value = prompt;
  sendCommand();
}

async function runMacro(macroName) {
  appendLog("user", `❯ Macro déclenchée : ${macroName}`);
  if (macroName === "quick_diagnostic") {
    executeQuick("Effectue un diagnostic complet de mon PC (CPU, RAM, espace disque et processus clés).");
  } else if (macroName === "capture_desktop") {
    executeQuick("Prends une capture d'écran du bureau et montre-moi le résultat.");
  }
}

// Chargement de la liste des outils
async function fetchTools() {
  try {
    const res = await fetch("/api/tools");
    const tools = await res.json();
    toolsList.innerHTML = "";
    tools.forEach(t => {
      const item = document.createElement("div");
      item.className = "tool-item";
      item.innerHTML = `
        <div class="tool-name">${t.name}</div>
        <div class="tool-desc">${t.description}</div>
      `;
      toolsList.appendChild(item);
    });
  } catch (e) {
    console.error("Erreur chargement outils:", e);
  }
}

// Polling périodique des métriques hardware
setInterval(async () => {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    updateStatus(data.agent);
    updateHardware(data.hardware);
  } catch (e) {}
}, 3000);

// Initialisation
window.addEventListener("DOMContentLoaded", () => {
  connectWebSocket();
  fetchTools();
});
