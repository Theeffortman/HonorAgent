const state = {
  agents: [],
  tasks: [],
};

const $ = (selector) => document.querySelector(selector);

function setLog(payload) {
  $("#outputLog").textContent = JSON.stringify(payload, null, 2);
}

function setStatus(ok, text) {
  const dot = $("#apiStatus");
  dot.className = `status-dot ${ok ? "ok" : "fail"}`;
  $("#apiStatusText").textContent = text;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  setLog({ status: response.status, path, response: data });
  if (!response.ok) {
    const detail = typeof data === "object" ? data.detail || data.message : data;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return data;
}

function renderAgents() {
  const list = $("#agentList");
  const choices = $("#agentChoices");
  list.innerHTML = "";
  choices.innerHTML = "";

  state.agents.forEach((agent, index) => {
    const row = document.createElement("article");
    row.className = "agent-row";
    row.innerHTML = `
      <div class="agent-title">${agent.name}<span class="badge">${agent.id}</span></div>
      <div class="meta">${agent.description}</div>
      <div class="capabilities">
        ${agent.capabilities.map((capability) => `<span class="badge">${capability}</span>`).join("")}
      </div>
    `;
    list.appendChild(row);

    const label = document.createElement("label");
    label.className = "choice";
    label.innerHTML = `
      <input type="checkbox" name="agents" value="${agent.id}" ${index === 0 ? "checked" : ""} />
      <span>${agent.name}</span>
    `;
    choices.appendChild(label);
  });
}

function renderTasks() {
  const list = $("#taskList");
  list.innerHTML = "";

  if (!state.tasks.length) {
    list.innerHTML = `<div class="task-row"><div class="meta">暂无任务</div></div>`;
    return;
  }

  state.tasks.forEach((task) => {
    const row = document.createElement("article");
    row.className = "task-row";
    row.innerHTML = `
      <div>
        <div class="task-title">
          ${task.name}
          <span class="badge ${task.status}">${task.status}</span>
          <span class="badge ${task.priority}">${task.priority}</span>
        </div>
        <div class="meta">${task.description || "无描述"}</div>
        <div class="meta">ID: ${task.id} · Agents: ${task.agents.join(", ") || "未指定"}</div>
      </div>
      <div class="row-actions">
        <button class="secondary" data-detail="${task.id}" type="button">详情</button>
        <button data-run="${task.id}" type="button">运行</button>
      </div>
    `;
    list.appendChild(row);
  });
}

async function checkHealth() {
  try {
    const data = await request("/health");
    setStatus(true, `${data.service}: ${data.status}`);
  } catch (error) {
    setStatus(false, error.message);
  }
}

async function loadAgents() {
  const data = await request("/api/v1/agents");
  state.agents = data.data;
  renderAgents();
}

async function loadTasks() {
  const data = await request("/api/v1/tasks");
  state.tasks = data.data;
  renderTasks();
}

async function createTask(event) {
  event.preventDefault();
  const agents = [...document.querySelectorAll('input[name="agents"]:checked')].map((input) => input.value);
  const payload = {
    name: $("#taskName").value.trim(),
    description: $("#taskDescription").value.trim(),
    priority: $("#taskPriority").value,
    agents,
    params: {
      data_source: $("#taskDataSource").value.trim(),
      date_range: $("#taskDateRange").value.trim(),
    },
  };

  await request("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadTasks();
}

async function showTask(taskId) {
  await request(`/api/v1/tasks/${taskId}`);
}

async function runTask(taskId) {
  await request(`/api/v1/tasks/${taskId}/run`, { method: "POST" });
  await loadTasks();
}

function renderGithubInsight(insight) {
  $("#githubResult").innerHTML = `
    <div class="insight-grid">
      <div class="score">${insight.health_score}</div>
      <div>
        <div class="task-title">${insight.owner}/${insight.repo}</div>
        <div class="meta">${insight.url}</div>
      </div>
    </div>
    <h3>Signals</h3>
    <ul>${insight.signals.map((item) => `<li>${item}</li>`).join("") || "<li>无</li>"}</ul>
    <h3>Risks</h3>
    <ul>${insight.risks.map((item) => `<li>${item}</li>`).join("") || "<li>无</li>"}</ul>
    <h3>Suggested Tasks</h3>
    <ul>${insight.suggested_tasks.map((item) => `<li>${item}</li>`).join("") || "<li>无</li>"}</ul>
  `;
}

async function analyzeGithub(event) {
  event.preventDefault();
  const data = await request("/api/v1/github/analyze", {
    method: "POST",
    body: JSON.stringify({
      url: $("#githubUrl").value.trim(),
      include_remote: $("#includeRemote").checked,
    }),
  });
  renderGithubInsight(data.data);
}

function bindEvents() {
  $("#refreshAll").addEventListener("click", refreshAll);
  $("#loadAgents").addEventListener("click", loadAgents);
  $("#loadTasks").addEventListener("click", loadTasks);
  $("#taskForm").addEventListener("submit", createTask);
  $("#githubForm").addEventListener("submit", analyzeGithub);
  $("#clearLog").addEventListener("click", () => setLog({}));

  $("#taskList").addEventListener("click", (event) => {
    const detailId = event.target.dataset.detail;
    const runId = event.target.dataset.run;
    if (detailId) showTask(detailId);
    if (runId) runTask(runId);
  });
}

async function refreshAll() {
  await checkHealth();
  await Promise.all([loadAgents(), loadTasks()]);
}

bindEvents();
refreshAll().catch((error) => {
  setStatus(false, error.message);
  setLog({ error: error.message });
});
