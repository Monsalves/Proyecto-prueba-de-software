const operationSpecs = {
  list: [
    { title: "CREATE", description: "Crear una nueva lista remota.", obj: "LIST", op: "CREATE", fields: [] },
    { title: "INSERT", description: "Insertar valor al final.", obj: "LIST", op: "INSERT", fields: ["instance_id", "data"] },
    { title: "GET", description: "Leer por posicion.", obj: "LIST", op: "GET", fields: ["instance_id", "data"], labels: { data: "Posicion" } },
    { title: "REMOVE", description: "Eliminar por posicion.", obj: "LIST", op: "REMOVE", fields: ["instance_id", "data"], labels: { data: "Posicion" } },
    { title: "SIZE", description: "Consultar tamano.", obj: "LIST", op: "SIZE", fields: ["instance_id"] },
    { title: "CONTAINS", description: "Buscar valor.", obj: "LIST", op: "CONTAINS", fields: ["instance_id", "data"] },
  ],
  stack: [
    { title: "CREATE", description: "Crear una nueva pila remota.", obj: "STACK", op: "CREATE", fields: [] },
    { title: "PUSH", description: "Apilar valor.", obj: "STACK", op: "PUSH", fields: ["instance_id", "data"] },
    { title: "POP", description: "Desapilar y devolver tope.", obj: "STACK", op: "POP", fields: ["instance_id"] },
    { title: "PEEK", description: "Consultar tope.", obj: "STACK", op: "PEEK", fields: ["instance_id"] },
    { title: "IS_EMPTY", description: "Indicar si esta vacia.", obj: "STACK", op: "IS_EMPTY", fields: ["instance_id"] },
  ],
  tree: [
    { title: "CREATE", description: "Crear un arbol BST remoto.", obj: "TREE", op: "CREATE", fields: [] },
    { title: "INSERT", description: "Insertar valor.", obj: "TREE", op: "INSERT", fields: ["instance_id", "data"] },
    { title: "SEARCH", description: "Buscar valor.", obj: "TREE", op: "SEARCH", fields: ["instance_id", "data"] },
    { title: "DELETE", description: "Eliminar valor.", obj: "TREE", op: "DELETE", fields: ["instance_id", "data"] },
    { title: "INORDER", description: "Consultar recorrido inorden.", obj: "TREE", op: "INORDER", fields: ["instance_id"] },
  ],
};

const state = {
  sessions: [],
  activeSessionId: null,
};

const elements = {
  activeSessionName: document.querySelector("#active-session-name"),
  activeSessionId: document.querySelector("#active-session-id"),
  activeSessionPid: document.querySelector("#active-session-pid"),
  sessionCount: document.querySelector("#session-count"),
  endpointPreview: document.querySelector("#endpoint-preview"),
  sidebarEndpoint: document.querySelector("#sidebar-endpoint"),
  sessionTabs: document.querySelector("#session-tabs"),
  status: document.querySelector("#connection-status"),
  history: document.querySelector("#history"),
  historyCaption: document.querySelector("#history-caption"),
  connectForm: document.querySelector("#connect-form"),
  disconnectBtn: document.querySelector("#disconnect-btn"),
  preloadBtn: document.querySelector("#preload-btn"),
  clearHistoryBtn: document.querySelector("#clear-history-btn"),
  rawMessage: document.querySelector("#raw-message"),
  sendRawBtn: document.querySelector("#send-raw-btn"),
  newSessionBtn: document.querySelector("#new-session-btn"),
  template: document.querySelector("#action-card-template"),
};

boot().catch((error) => {
  renderBootError(String(error));
});

async function boot() {
  renderActionCards();
  bindEvents();
  wireStructureTabs();
  await createSession();
}

function bindEvents() {
  elements.connectForm.addEventListener("submit", handleConnect);
  elements.disconnectBtn.addEventListener("click", handleDisconnect);
  elements.preloadBtn.addEventListener("click", handlePreload);
  elements.clearHistoryBtn.addEventListener("click", clearActiveHistory);
  elements.sendRawBtn.addEventListener("click", handleRawSend);
  elements.newSessionBtn.addEventListener("click", createSession);
}

function wireStructureTabs() {
  const tabs = Array.from(document.querySelectorAll(".structure-tab"));
  const panels = Array.from(document.querySelectorAll(".structure-panel"));
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach((item) => item.classList.toggle("is-active", item === tab));
      panels.forEach((panel) => panel.classList.toggle("is-active", panel.dataset.panel === target));
    });
  });
}

function renderActionCards() {
  for (const [key, specs] of Object.entries(operationSpecs)) {
    const container = document.querySelector(`#${key}-actions`);
    const select = document.querySelector(`#${key}-select`);
    
    if (select) {
      select.innerHTML = "";
      specs.forEach((spec) => {
        const option = document.createElement("option");
        option.value = spec.title;
        option.textContent = spec.title;
        select.appendChild(option);
      });
      
      select.addEventListener("change", () => {
        const activeValue = select.value;
        const cards = container.querySelectorAll(".action-card");
        cards.forEach((card) => {
          card.style.display = card.dataset.action === activeValue ? "flex" : "none";
        });
      });
    }

    specs.forEach((spec) => container.appendChild(buildActionCard(spec)));

    if (select && specs.length > 0) {
      select.value = specs[0].title;
      setTimeout(() => {
        const cards = container.querySelectorAll(".action-card");
        cards.forEach((card) => {
          card.style.display = card.dataset.action === specs[0].title ? "flex" : "none";
        });
      }, 0);
    }
  }
}

function buildActionCard(spec) {
  const fragment = elements.template.content.cloneNode(true);
  const form = fragment.querySelector("form");
  form.dataset.action = spec.title;
  
  fragment.querySelector("h3").textContent = spec.title;
  fragment.querySelector("p").textContent = spec.description;

  const fieldList = fragment.querySelector(".field-list");
  spec.fields.forEach((field) => {
    const label = document.createElement("label");
    const span = document.createElement("span");
    span.textContent = spec.labels?.[field] ?? humanizeField(field);
    const input = document.createElement("input");
    input.name = field;
    input.type = "number";
    input.placeholder = span.textContent;
    label.append(span, input);
    fieldList.append(label);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await handleStructuredRequest(spec, new FormData(form));
  });

  return fragment;
}

async function createSession() {
  const payload = await apiGet("/api/session");
  const index = state.sessions.length + 1;
  const session = {
    id: payload.session_id,
    pid: payload.pid ?? null,
    name: `Sesion ${index}`,
    host: "127.0.0.1",
    port: 9999,
    connected: false,
    history: [],
    rawMessage: "LIST|CREATE|0|",
  };

  state.sessions.push(session);
  state.activeSessionId = session.id;
  appendSessionHistory(session.id, "SESION", true, { response: `Sesion local creada: ${session.id}` });
  await initializeSession(session);
  renderSessionTabs();
  syncSessionToView();
}

async function initializeSession(session) {
  const connectResult = await apiPost("/api/connect", {
    session_id: session.id,
    host: session.host,
    port: session.port,
  });
  session.pid = connectResult.pid ?? session.pid;
  session.connected = Boolean(connectResult.ok);
  appendSessionHistory(session.id, "AUTO CONNECT", connectResult.ok, connectResult);

  if (!connectResult.ok) {
    return;
  }

  const preloadResult = await apiPost("/api/preload", { session_id: session.id });
  appendSessionHistory(session.id, "AUTO PRECARGA", preloadResult.ok, preloadResult);
}

function getActiveSession() {
  return state.sessions.find((session) => session.id === state.activeSessionId) || null;
}

function renderSessionTabs() {
  elements.sessionTabs.innerHTML = "";
  state.sessions.forEach((session) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `session-tab ${session.id === state.activeSessionId ? "is-active" : ""}`;
    button.innerHTML = `
      <div class="session-tab-top">
        <span class="session-tab-title">${session.name}</span>
        <span class="session-dot ${session.connected ? "is-online" : ""}"></span>
      </div>
      <div class="session-tab-meta">${session.connected ? `${session.host}:${session.port}` : "Sin conexion"}</div>
      <div class="session-tab-meta">PID ${session.pid ?? "-"}</div>
    `;
    button.addEventListener("click", () => {
      state.activeSessionId = session.id;
      renderSessionTabs();
      syncSessionToView();
    });
    elements.sessionTabs.append(button);
  });
  elements.sessionCount.textContent = String(state.sessions.length);
}

function syncSessionToView() {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  elements.activeSessionName.textContent = session.name;
  elements.activeSessionId.textContent = session.id;
  elements.activeSessionPid.textContent = session.pid ?? "-";
  elements.endpointPreview.textContent = `${session.host}:${session.port}`;
  elements.sidebarEndpoint.textContent = `${session.host}:${session.port}`;
  elements.connectForm.host.value = session.host;
  elements.connectForm.port.value = String(session.port);
  elements.rawMessage.value = session.rawMessage;
  renderConnectionStatus(session.connected, session.connected ? `${session.host}:${session.port}` : "Desconectado");
  renderHistory(session);
}

function renderConnectionStatus(connected, detail) {
  elements.status.textContent = connected ? `Conectado a ${detail}` : detail;
  elements.status.classList.toggle("is-online", connected);
  elements.status.classList.toggle("is-offline", !connected);
}

function renderHistory(session) {
  elements.historyCaption.textContent = `Respuestas y errores de ${session.name}.`;
  elements.history.innerHTML = "";
  if (session.history.length === 0) {
    elements.history.innerHTML = '<div class="empty-state">Aun no hay actividad en esta sesion.</div>';
    return;
  }

  session.history.forEach((entry) => {
    elements.history.append(buildHistoryNode(entry));
  });
}

function buildHistoryNode(entry) {
  const article = document.createElement("article");
  article.className = `log-entry ${entry.ok ? "ok" : "error"}`;

  const meta = document.createElement("div");
  meta.className = "log-meta";
  meta.innerHTML = `<strong>${entry.label}</strong><span>${entry.ok ? "OK" : "ERROR"} · ${entry.time}</span>`;

  const pre = document.createElement("pre");
  pre.textContent = formatPayload(entry.payload);

  article.append(meta, pre);
  return article;
}

function appendSessionHistory(sessionId, label, ok, payload) {
  const session = state.sessions.find((item) => item.id === sessionId);
  if (!session) {
    return;
  }

  session.history.unshift({
    label,
    ok,
    payload,
    time: new Date().toLocaleTimeString(),
  });

  if (session.id === state.activeSessionId) {
    renderHistory(session);
  }
}

function clearActiveHistory() {
  const session = getActiveSession();
  if (!session) {
    return;
  }
  session.history = [];
  renderHistory(session);
}

async function handleConnect(event) {
  event.preventDefault();
  const session = getActiveSession();
  if (!session) {
    return;
  }

  const formData = new FormData(elements.connectForm);
  session.host = String(formData.get("host") || "127.0.0.1").trim();
  session.port = Number(formData.get("port")) || 9999;

  const result = await apiPost("/api/connect", {
    session_id: session.id,
    host: session.host,
    port: session.port,
  });

  session.pid = result.pid ?? session.pid;
  session.connected = Boolean(result.ok);
  renderSessionTabs();
  syncSessionToView();
  appendSessionHistory(session.id, "CONNECT", result.ok, result);
}

async function handleDisconnect() {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  const result = await apiPost("/api/disconnect", { session_id: session.id });
  session.pid = result.pid ?? session.pid;
  session.connected = false;
  renderSessionTabs();
  syncSessionToView();
  appendSessionHistory(session.id, "DISCONNECT", result.ok, result);
}

async function handlePreload() {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  const result = await apiPost("/api/preload", { session_id: session.id });
  appendSessionHistory(session.id, "PRECARGA", result.ok, result);
}

async function handleRawSend() {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  session.rawMessage = elements.rawMessage.value;
  const result = await apiPost("/api/raw", {
    session_id: session.id,
    raw_message: session.rawMessage,
  });
  appendSessionHistory(session.id, "RAW", result.ok, result);
}

async function handleStructuredRequest(spec, formData) {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  const instanceId = spec.fields.includes("instance_id") ? Number(formData.get("instance_id")) : 0;
  const rawData = spec.fields.includes("data") ? formData.get("data") : "";

  const result = await apiPost("/api/request", {
    session_id: session.id,
    obj_type: spec.obj,
    operation: spec.op,
    instance_id: Number.isNaN(instanceId) ? 0 : instanceId,
    data: rawData === null ? "" : String(rawData),
  });

  appendSessionHistory(session.id, `${spec.obj} ${spec.op}`, result.ok, result);
}

function renderBootError(error) {
  elements.history.innerHTML = "";
  const block = document.createElement("div");
  block.className = "empty-state";
  block.textContent = `No se pudo inicializar la interfaz: ${error}`;
  elements.history.append(block);
}

function humanizeField(field) {
  if (field === "instance_id") return "ID de instancia";
  if (field === "data") return "Valor";
  return field;
}

function formatPayload(payload) {
  if (typeof payload === "string") {
    return payload;
  }
  
  if (payload && typeof payload === "object") {
    // If it has raw_request and raw_response, emulate terminal session
    if (payload.raw_request && payload.raw_response) {
      return `> ${payload.raw_request}\n< ${payload.raw_response.trim()}`;
    }
    
    // For connect / disconnect
    if (payload.hasOwnProperty("connected")) {
      if (payload.ok) {
        return `CONNECT -> ${payload.connected ? "CONECTADO A " + (payload.host || "") + ":" + (payload.port || "") : "DESCONECTADO"}`;
      } else {
        return `ERROR: ${payload.error || "No se pudo cambiar el estado de conexion"}`;
      }
    }
    
    // For preload
    if (payload.response && typeof payload.response === "object") {
      const resp = payload.response;
      if (resp.list_id !== undefined) {
        return `PRECARGA -> OK\n\n` +
               `LIST Creada (ID: ${resp.list_id})\n` +
               `  Valores: [${resp.list_values?.join(", ")}]\n` +
               `STACK Creada (ID: ${resp.stack_id})\n` +
               `  Tope: ${resp.stack_top}\n` +
               `TREE Creada (ID: ${resp.tree_id})\n` +
               `  Recorrido inorden: [${resp.tree_inorder?.join(", ")}]`;
      }
    }

    if (payload.error) {
      return `ERROR: ${payload.error}`;
    }

    if (payload.response) {
      return String(payload.response);
    }
    
    return JSON.stringify(payload, null, 2);
  }
  
  return String(payload);
}

async function apiGet(url) {
  const response = await fetch(url, { method: "GET" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function apiPost(url, payload) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      return { ok: false, error: data.error || `HTTP ${response.status}` };
    }
    return data;
  } catch (error) {
    return { ok: false, error: String(error) };
  }
}
