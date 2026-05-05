// ============================================================
// Control Panel - vanilla JS SPA
// ============================================================

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDate = (s) => s ? new Date(s.includes("T") ? s : s.replace(" ", "T") + "Z").toLocaleString() : "-";
const fmtBytes = (n) => {
  if (n == null) return "-";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
};

async function api(path, opts = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

function toast(msg, kind = "") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = `toast show ${kind}`;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 3000);
}

function modal(html, onMount) {
  const m = $("#modal");
  $("#modalCard").innerHTML = html;
  m.classList.remove("hidden");
  if (onMount) onMount($("#modalCard"));
  m.onclick = (e) => { if (e.target === m) closeModal(); };
}

function closeModal() {
  $("#modal").classList.add("hidden");
  $("#modalCard").innerHTML = "";
}

// ============================================================
// Router
// ============================================================

const routes = {
  dashboard: renderDashboard,
  scripts: renderScripts,
  tasks: renderTasks,
  notes: renderNotes,
  update: renderUpdate,
  settings: renderSettings,
};

function navigate() {
  const tab = (location.hash || "#dashboard").slice(1).split("?")[0] || "dashboard";
  $$(".tabs a").forEach(a => a.classList.toggle("active", a.dataset.tab === tab));
  const fn = routes[tab] || renderDashboard;
  fn().catch(err => {
    console.error(err);
    $("#content").innerHTML = `<div class="card"><h3>Error</h3><pre class="console">${esc(err.message)}</pre></div>`;
  });
}

window.addEventListener("hashchange", navigate);

// ============================================================
// Dashboard
// ============================================================

async function renderDashboard() {
  const d = await api("/dashboard");
  $("#versionTag").textContent = `v${d.version}`;

  const metricCards = (d.custom_metrics || []).map(m => `
    <div class="metric">
      <div class="label">${esc(m.label)}</div>
      <div class="value">${esc(m.value)}${m.unit ? ` <span class="sub">${esc(m.unit)}</span>` : ""}</div>
      <div class="sub">${fmtDate(m.updated_at)}</div>
    </div>
  `).join("");

  $("#content").innerHTML = `
    <div class="toolbar">
      <h2 style="margin:0">Dashboard</h2>
      <div class="spacer"></div>
      <button class="btn btn-sm" onclick="addMetricModal()">+ Custom metric</button>
    </div>

    <div class="grid grid-4">
      <div class="metric">
        <div class="label">Tasks - Backlog</div>
        <div class="value">${d.tasks.backlog}</div>
      </div>
      <div class="metric">
        <div class="label">Tasks - Doing</div>
        <div class="value">${d.tasks.doing}</div>
      </div>
      <div class="metric">
        <div class="label">Tasks - Done</div>
        <div class="value">${d.tasks.done}</div>
      </div>
      <div class="metric">
        <div class="label">Scripts run today</div>
        <div class="value">${d.scripts_today}</div>
      </div>
      <div class="metric">
        <div class="label">Notes</div>
        <div class="value">${d.notes_total}</div>
      </div>
      <div class="metric">
        <div class="label">Last backup</div>
        <div class="value" style="font-size:13px;">${d.last_backup ? esc(d.last_backup.status) : "never"}</div>
        <div class="sub">${d.last_backup ? fmtDate(d.last_backup.created_at) : ""}</div>
      </div>
      <div class="metric">
        <div class="label">Last script</div>
        <div class="value" style="font-size:13px;">${d.last_script ? esc(d.last_script.script_path) : "never"}</div>
        <div class="sub">${d.last_script ? `exit ${d.last_script.exit_code}` : ""}</div>
      </div>
      <div class="metric">
        <div class="label">Version</div>
        <div class="value" style="font-size:13px;">${esc(d.version)}</div>
      </div>
      ${metricCards}
    </div>

    <div class="grid grid-2" style="margin-top:24px;">
      <div class="card">
        <h3>Upcoming due</h3>
        ${(d.upcoming_due && d.upcoming_due.length) ? `
          <table>
            <thead><tr><th>Title</th><th>Due</th><th>Priority</th></tr></thead>
            <tbody>
              ${d.upcoming_due.map(t => `
                <tr>
                  <td>${esc(t.title)}</td>
                  <td>${esc(t.due_date)}</td>
                  <td><span class="badge ${t.priority === 'high' ? 'red' : t.priority === 'low' ? 'blue' : ''}">${esc(t.priority)}</span></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        ` : `<div class="empty">No tasks with due dates.</div>`}
      </div>

      <div class="card">
        <h3>Recent script runs</h3>
        ${(d.recent_runs && d.recent_runs.length) ? `
          <table>
            <thead><tr><th>Script</th><th>When</th><th>Exit</th><th>Duration</th></tr></thead>
            <tbody>
              ${d.recent_runs.map(r => `
                <tr>
                  <td class="mono">${esc(r.script_path)}</td>
                  <td>${fmtDate(r.started_at)}</td>
                  <td><span class="badge ${r.exit_code === 0 ? 'green' : 'red'}">${r.exit_code ?? "-"}</span></td>
                  <td>${r.duration_seconds != null ? r.duration_seconds.toFixed(1) + "s" : "-"}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        ` : `<div class="empty">No runs yet.</div>`}
      </div>
    </div>
  `;
}

window.addMetricModal = function() {
  modal(`
    <h3>Add or update custom metric</h3>
    <label>Key (unique id, no spaces)</label><input id="mk" placeholder="e.g. weekly_sales">
    <label>Label (display name)</label><input id="ml" placeholder="e.g. Weekly Sales">
    <label>Value</label><input id="mv" type="number" step="any" placeholder="123.45">
    <label>Unit (optional)</label><input id="mu" placeholder="e.g. EUR, %, items">
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveMetric()">Save</button>
    </div>
  `);
};

window.saveMetric = async function() {
  const key = $("#mk").value.trim();
  const label = $("#ml").value.trim();
  const value = $("#mv").value;
  const unit = $("#mu").value.trim() || null;
  if (!key || !label || value === "") { toast("Key, label and value required", "error"); return; }
  await api("/dashboard/metrics", { method: "PUT", body: JSON.stringify({ key, label, value: parseFloat(value), unit }) });
  closeModal();
  toast("Metric saved", "success");
  navigate();
};

window.closeModal = closeModal;

// ============================================================
// Scripts
// ============================================================

async function renderScripts() {
  const [data, runs, pathInfo] = await Promise.all([
    api("/scripts"),
    api("/scripts/runs?limit=20"),
    api("/scripts/path"),
  ]);

  $("#content").innerHTML = `
    <div class="toolbar">
      <h2 style="margin:0">Scripts</h2>
      <div class="spacer"></div>
      <span class="muted mono">${esc(data.scripts_path)}</span>
      ${pathInfo.is_override ? `<span class="badge purple">override</span>` : ""}
      <button class="btn btn-sm" onclick="changeScriptsPath()">Change folder</button>
      ${pathInfo.is_override ? `<button class="btn btn-sm" onclick="resetScriptsPath()">Reset to default</button>` : ""}
    </div>

    ${!data.exists ? `
      <div class="card">
        <h3>Scripts folder not found</h3>
        <p class="muted">Path: <span class="mono">${esc(data.scripts_path)}</span></p>
        <p class="muted">Click "Change folder" above to point to a folder with your <span class="mono">.ps1</span> / <span class="mono">.py</span> / <span class="mono">.bat</span> / <span class="mono">.sh</span> files. Sidecar <span class="mono">name.meta.json</span> with <span class="mono">{ "name": "...", "description": "...", "args": "..." }</span> is optional.</p>
      </div>
    ` : data.scripts.length === 0 ? `
      <div class="card empty">No scripts found in <span class="mono">${esc(data.scripts_path)}</span>.</div>
    ` : `
      <div class="card">
        <table>
          <thead><tr><th>Name</th><th>Path</th><th>Lang</th><th>Modified</th><th>Run</th></tr></thead>
          <tbody>
            ${data.scripts.map(s => `
              <tr>
                <td>
                  <div style="font-weight:500;">${esc(s.name)}</div>
                  ${s.description ? `<div class="muted" style="font-size:12px;">${esc(s.description)}</div>` : ""}
                </td>
                <td class="mono">${esc(s.path)}</td>
                <td><span class="badge blue">${esc(s.language)}</span></td>
                <td class="muted">${esc(s.modified_at)}</td>
                <td>
                  <button class="btn btn-sm btn-primary" onclick='runScript(${JSON.stringify(s.path)}, ${JSON.stringify(s.args_help || "")})'>Run</button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `}

    <div class="card" style="margin-top:24px;">
      <h3>Recent runs</h3>
      ${runs.length === 0 ? `<div class="empty">No runs yet.</div>` : `
        <table>
          <thead><tr><th>Script</th><th>Started</th><th>Exit</th><th>Duration</th><th>Output</th></tr></thead>
          <tbody>
            ${runs.map(r => `
              <tr>
                <td class="mono">${esc(r.script_path)}</td>
                <td>${fmtDate(r.started_at)}</td>
                <td><span class="badge ${r.exit_code === 0 ? 'green' : r.exit_code == null ? 'yellow' : 'red'}">${r.exit_code ?? "running"}</span></td>
                <td>${r.duration_seconds != null ? r.duration_seconds.toFixed(2) + "s" : "-"}</td>
                <td><button class="btn btn-sm" onclick="viewRun(${r.id})">View</button></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `}
    </div>
  `;
}

window.changeScriptsPath = async function() {
  const current = await api("/scripts/path");
  modal(`
    <h3>Change scripts folder</h3>
    <p class="muted">Currently: <span class="mono">${esc(current.path)}</span></p>
    <p class="muted">Default (env var <span class="mono">CP_SCRIPTS_PATH</span>): <span class="mono">${esc(current.default_path)}</span></p>
    <label>New folder path (paste full Windows path)</label>
    <input id="newPath" placeholder="C:\\Users\\...\\my scripts" autofocus>
    <p class="muted" style="font-size:11px;margin-top:8px;">Folder must already exist on this machine. The override is stored in the SQLite settings table and persists across restarts. Reset to default any time.</p>
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveScriptsPath()">Save</button>
    </div>
  `, () => $("#newPath").focus());
};

window.saveScriptsPath = async function() {
  const path = $("#newPath").value.trim();
  if (!path) { toast("Path required", "error"); return; }
  try {
    const r = await api("/scripts/path", { method: "PUT", body: JSON.stringify({ path }) });
    closeModal();
    toast(`Scripts folder set to ${r.path}`, "success");
    navigate();
  } catch (err) {
    toast(err.message, "error");
  }
};

window.resetScriptsPath = async function() {
  if (!confirm("Reset to the default scripts folder (CP_SCRIPTS_PATH env var)?")) return;
  await api("/scripts/path", { method: "DELETE" });
  toast("Reset to default", "success");
  navigate();
};

window.runScript = function(path, argsHelp) {
  modal(`
    <h3>Run: <span class="mono">${esc(path)}</span></h3>
    ${argsHelp ? `<p class="muted">Args hint: <span class="mono">${esc(argsHelp)}</span></p>` : ""}
    <label>Arguments (optional)</label>
    <input id="runArgs" placeholder="space-separated args">
    <label>Timeout (seconds)</label>
    <input id="runTimeout" type="number" value="300">
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick='execRun(${JSON.stringify(path)})'>Run</button>
    </div>
  `);
};

window.execRun = async function(path) {
  const args = $("#runArgs").value.trim() || null;
  const timeout = parseInt($("#runTimeout").value) || 300;
  $("#modalCard").innerHTML = `<h3>Running...</h3><pre class="console" id="liveOut">starting...</pre>`;
  try {
    const result = await api("/scripts/run", {
      method: "POST",
      body: JSON.stringify({ script_path: path, args, timeout_seconds: timeout }),
    });
    $("#modalCard").innerHTML = `
      <h3>Run finished - exit ${result.exit_code}</h3>
      <p class="muted">Duration: ${result.duration_seconds.toFixed(2)}s</p>
      <h3>stdout</h3>
      <pre class="console">${esc(result.stdout || "(empty)")}</pre>
      <h3>stderr</h3>
      <pre class="console">${esc(result.stderr || "(empty)")}</pre>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="closeModal(); navigate();">Close</button>
      </div>
    `;
  } catch (err) {
    $("#modalCard").innerHTML = `<h3>Failed</h3><pre class="console">${esc(err.message)}</pre><div class="modal-actions"><button class="btn" onclick="closeModal()">Close</button></div>`;
  }
};

window.viewRun = async function(id) {
  const r = await api(`/scripts/runs/${id}`);
  modal(`
    <h3>${esc(r.script_path)} - exit ${r.exit_code ?? "(running)"}</h3>
    <p class="muted">${fmtDate(r.started_at)} - ${r.duration_seconds != null ? r.duration_seconds.toFixed(2) + "s" : "-"}</p>
    <h3>stdout</h3>
    <pre class="console">${esc(r.stdout || "(empty)")}</pre>
    <h3>stderr</h3>
    <pre class="console">${esc(r.stderr || "(empty)")}</pre>
    <div class="modal-actions"><button class="btn" onclick="closeModal()">Close</button></div>
  `);
};

// ============================================================
// Tasks (kanban)
// ============================================================

async function renderTasks() {
  const tasks = await api("/tasks");
  const cols = { backlog: [], doing: [], done: [] };
  tasks.forEach(t => cols[t.status]?.push(t));

  $("#content").innerHTML = `
    <div class="toolbar">
      <h2 style="margin:0">Tasks</h2>
      <div class="spacer"></div>
      <button class="btn btn-primary" onclick="newTaskModal()">+ New task</button>
    </div>

    <div class="kanban">
      ${["backlog", "doing", "done"].map(status => `
        <div class="column" data-status="${status}" ondragover="event.preventDefault(); this.classList.add('drag-over')" ondragleave="this.classList.remove('drag-over')" ondrop="dropTask(event, '${status}')">
          <h3>${status.toUpperCase()} <span class="count">${cols[status].length}</span></h3>
          ${cols[status].map(t => `
            <div class="kanban-card" draggable="true" ondragstart="event.dataTransfer.setData('text/plain', '${t.id}'); this.classList.add('dragging')" ondragend="this.classList.remove('dragging')" data-id="${t.id}">
              <div class="title">${esc(t.title)}</div>
              ${t.description ? `<div class="muted" style="font-size:12px;margin-bottom:6px;">${esc(t.description.slice(0, 100))}${t.description.length > 100 ? "..." : ""}</div>` : ""}
              <div class="meta">
                <span class="badge ${t.priority === 'high' ? 'red' : t.priority === 'low' ? 'blue' : ''}">${esc(t.priority)}</span>
                ${t.due_date ? `<span class="badge yellow">${esc(t.due_date)}</span>` : ""}
                <span class="spacer"></span>
                <a href="#" onclick="event.preventDefault(); editTask(${t.id})" class="muted">edit</a>
                <a href="#" onclick="event.preventDefault(); deleteTask(${t.id})" class="muted">x</a>
              </div>
            </div>
          `).join("")}
        </div>
      `).join("")}
    </div>
  `;
}

window.newTaskModal = function() {
  modal(`
    <h3>New task</h3>
    <label>Title</label><input id="tt" autofocus>
    <label>Description</label><textarea id="td" rows="3"></textarea>
    <label>Status</label>
    <select id="ts"><option value="backlog">backlog</option><option value="doing">doing</option><option value="done">done</option></select>
    <label>Priority</label>
    <select id="tp"><option value="normal">normal</option><option value="high">high</option><option value="low">low</option></select>
    <label>Due date (YYYY-MM-DD, optional)</label><input id="tdd" type="date">
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveTask()">Create</button>
    </div>
  `, () => $("#tt").focus());
};

window.saveTask = async function(id) {
  const payload = {
    title: $("#tt").value.trim(),
    description: $("#td").value.trim() || null,
    status: $("#ts").value,
    priority: $("#tp").value,
    due_date: $("#tdd").value || null,
  };
  if (!payload.title) { toast("Title required", "error"); return; }
  if (id) await api(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
  else await api("/tasks", { method: "POST", body: JSON.stringify(payload) });
  closeModal();
  toast("Saved", "success");
  navigate();
};

window.editTask = async function(id) {
  const tasks = await api("/tasks");
  const t = tasks.find(x => x.id === id);
  if (!t) return;
  modal(`
    <h3>Edit task</h3>
    <label>Title</label><input id="tt" value="${esc(t.title)}">
    <label>Description</label><textarea id="td" rows="3">${esc(t.description || "")}</textarea>
    <label>Status</label>
    <select id="ts">
      ${["backlog", "doing", "done"].map(s => `<option value="${s}" ${s === t.status ? "selected" : ""}>${s}</option>`).join("")}
    </select>
    <label>Priority</label>
    <select id="tp">
      ${["low", "normal", "high"].map(p => `<option value="${p}" ${p === t.priority ? "selected" : ""}>${p}</option>`).join("")}
    </select>
    <label>Due date</label><input id="tdd" type="date" value="${esc(t.due_date || "")}">
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveTask(${id})">Save</button>
    </div>
  `);
};

window.deleteTask = async function(id) {
  if (!confirm("Delete this task?")) return;
  await api(`/tasks/${id}`, { method: "DELETE" });
  toast("Deleted", "success");
  navigate();
};

window.dropTask = async function(e, status) {
  e.preventDefault();
  const id = parseInt(e.dataTransfer.getData("text/plain"));
  $$(".column").forEach(c => c.classList.remove("drag-over"));
  await api(`/tasks/${id}/move`, { method: "PATCH", body: JSON.stringify({ status, position: 0 }) });
  navigate();
};

// ============================================================
// Notes
// ============================================================

let _activeNote = null;

async function renderNotes() {
  const notes = await api("/notes");
  $("#content").innerHTML = `
    <div class="toolbar">
      <h2 style="margin:0">Notes</h2>
      <div class="spacer"></div>
      <button class="btn btn-primary" onclick="newNote()">+ New note</button>
    </div>

    <div class="note-list">
      <aside id="noteList">
        ${notes.length === 0 ? `<div class="empty">No notes yet.</div>` : notes.map(n => `
          <div class="note-item" data-id="${n.id}" onclick="loadNote(${n.id})">
            <div class="nt">${n.pinned ? "* " : ""}${esc(n.title)}</div>
            <div class="nm">${fmtDate(n.updated_at)}${n.tags ? " - " + esc(n.tags) : ""}</div>
          </div>
        `).join("")}
      </aside>
      <div class="card editor" id="noteEditor">
        <div class="empty">Select a note to view or edit.</div>
      </div>
    </div>
  `;
}

window.newNote = async function() {
  const n = await api("/notes", { method: "POST", body: JSON.stringify({ title: "Untitled", content: "" }) });
  navigate();
  setTimeout(() => loadNote(n.id), 100);
};

window.loadNote = async function(id) {
  const n = await api(`/notes/${id}`);
  _activeNote = n;
  $$(".note-item").forEach(el => el.classList.toggle("active", parseInt(el.dataset.id) === id));
  $("#noteEditor").innerHTML = `
    <div class="row">
      <input id="nTitle" value="${esc(n.title)}" style="font-size:16px;font-weight:500;">
    </div>
    <div class="row">
      <input id="nTags" value="${esc(n.tags || "")}" placeholder="tags (comma-separated)">
      <label class="row" style="margin:0;gap:6px;align-items:center;width:auto;">
        <input type="checkbox" id="nPinned" ${n.pinned ? "checked" : ""} style="width:auto;">
        Pinned
      </label>
    </div>
    <textarea id="nContent" placeholder="Markdown supported (rendered as plain text for now)">${esc(n.content)}</textarea>
    <div class="row">
      <button class="btn btn-primary" onclick="saveNote()">Save</button>
      <button class="btn btn-danger" onclick="deleteNote()">Delete</button>
      <span class="spacer"></span>
      <span class="muted">Updated ${fmtDate(n.updated_at)}</span>
    </div>
  `;
};

window.saveNote = async function() {
  if (!_activeNote) return;
  await api(`/notes/${_activeNote.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: $("#nTitle").value,
      content: $("#nContent").value,
      tags: $("#nTags").value || null,
      pinned: $("#nPinned").checked,
    }),
  });
  toast("Saved", "success");
  navigate();
};

window.deleteNote = async function() {
  if (!_activeNote) return;
  if (!confirm("Delete this note?")) return;
  await api(`/notes/${_activeNote.id}`, { method: "DELETE" });
  _activeNote = null;
  toast("Deleted", "success");
  navigate();
};

// ============================================================
// Update
// ============================================================

async function renderUpdate() {
  const info = await api("/update");
  const backups = await api("/backup");
  $("#content").innerHTML = `
    <h2>Update</h2>

    <div class="grid grid-2">
      <div class="card">
        <h3>Current version</h3>
        <div class="metric" style="margin-top:8px;">
          <div class="label">Installed</div>
          <div class="value mono">${esc(info.version)}</div>
          <div class="sub">platform: ${esc(info.platform)}</div>
        </div>
      </div>

      <div class="card">
        <h3>Repository</h3>
        <p class="muted">Source code lives at:</p>
        <p><a href="${esc(info.repo_url)}" target="_blank" class="mono">${esc(info.repo_url)}</a></p>
        <div class="row" style="margin-top:16px;gap:8px;">
          <a class="btn" href="${esc(info.repo_url)}" target="_blank">Open repo</a>
          <a class="btn" href="${esc(info.zip_url)}" target="_blank">Download ZIP</a>
          <button class="btn btn-primary" onclick="triggerUpdate()">Update now</button>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top:24px;">
      <h3>Recent backups (auto-created daily)</h3>
      ${backups.files.length === 0 ? `<div class="empty">No backups yet.</div>` : `
        <table>
          <thead><tr><th>File</th><th>Size</th><th>Modified</th></tr></thead>
          <tbody>
            ${backups.files.slice(0, 5).map(f => `
              <tr><td class="mono">${esc(f.name)}</td><td>${fmtBytes(f.size_bytes)}</td><td>${fmtDate(new Date(f.modified_at * 1000).toISOString())}</td></tr>
            `).join("")}
          </tbody>
        </table>
      `}
    </div>

    <div class="card" style="margin-top:24px;">
      <h3>How update works</h3>
      <ol class="muted">
        <li><b>Update now</b> launches <span class="mono">update.ps1</span> from your install dir (Windows only). It downloads the latest ZIP from GitHub, replaces files (keeps your DB and backups), and restarts the service.</li>
        <li>You can also re-run <span class="mono">setup.ps1</span> manually for the same effect plus dependency reinstall.</li>
        <li>Database file (<span class="mono">control_panel.db</span>) is preserved across updates.</li>
      </ol>
    </div>
  `;
}

window.triggerUpdate = async function() {
  if (!confirm("Trigger update? The service will restart and this page will briefly disconnect.")) return;
  try {
    const r = await api("/update/run", { method: "POST" });
    if (r.ok) toast("Update started. Service restarting...", "success");
    else toast(r.error || "Failed", "error");
  } catch (err) {
    toast(err.message, "error");
  }
};

// ============================================================
// Settings
// ============================================================

async function renderSettings() {
  const s = await api("/settings");
  const b = await api("/backup");

  $("#content").innerHTML = `
    <h2>Settings</h2>

    <div class="card">
      <h3>Environment</h3>
      <table>
        <tbody>
          ${Object.entries(s.env).map(([k, v]) => `
            <tr><td class="mono">${esc(k)}</td><td class="mono">${esc(v)}</td></tr>
          `).join("")}
          <tr><td class="mono">DB size</td><td>${fmtBytes(s.db_size_bytes)}</td></tr>
          <tr><td class="mono">Scripts folder exists</td><td>${s.scripts_path_exists ? "yes" : "no"}</td></tr>
        </tbody>
      </table>
      <p class="muted" style="margin-top:12px;">To change these, edit env vars on the service (NSSM AppEnvironmentExtra) or rerun setup.ps1.</p>
    </div>

    <div class="card" style="margin-top:24px;">
      <h3>Backups</h3>
      <div class="row" style="margin-bottom:12px;">
        <span class="muted">Daily at ${b.scheduled_hour}:00. Retention: ${b.retention_days} days. Path: <span class="mono">${esc(b.backup_path)}</span></span>
        <span class="spacer"></span>
        <button class="btn" onclick="manualBackup()">Backup now</button>
        <button class="btn" onclick="prunePackup()">Prune old</button>
      </div>
      ${b.files.length === 0 ? `<div class="empty">No backups yet.</div>` : `
        <table>
          <thead><tr><th>File</th><th>Size</th><th>Modified</th><th></th></tr></thead>
          <tbody>
            ${b.files.map(f => `
              <tr>
                <td class="mono">${esc(f.name)}</td>
                <td>${fmtBytes(f.size_bytes)}</td>
                <td>${fmtDate(new Date(f.modified_at * 1000).toISOString())}</td>
                <td><a class="btn btn-sm" href="/api/backup/download/${encodeURIComponent(f.name)}">Download</a></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `}
    </div>

    <div class="card" style="margin-top:24px;">
      <h3>User settings (key/value)</h3>
      <div class="row" style="margin-bottom:12px;">
        <input id="sk" placeholder="key" style="max-width:200px;">
        <input id="sv" placeholder="value">
        <button class="btn btn-primary" onclick="saveSetting()">Save</button>
      </div>
      ${s.user_settings.length === 0 ? `<div class="empty">No custom settings.</div>` : `
        <table>
          <thead><tr><th>Key</th><th>Value</th><th>Updated</th><th></th></tr></thead>
          <tbody>
            ${s.user_settings.map(u => `
              <tr>
                <td class="mono">${esc(u.key)}</td>
                <td class="mono">${esc(u.value)}</td>
                <td class="muted">${fmtDate(u.updated_at)}</td>
                <td><button class="btn btn-sm btn-danger" onclick="deleteSetting('${esc(u.key)}')">Delete</button></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `}
    </div>
  `;
}

window.manualBackup = async function() {
  const r = await api("/backup/run", { method: "POST" });
  if (r.ok) toast("Backup created", "success");
  else toast(r.error || "Failed", "error");
  navigate();
};

window.prunePackup = async function() {
  const r = await api("/backup/prune", { method: "POST" });
  toast(`Removed ${r.removed} old backups`, "success");
  navigate();
};

window.saveSetting = async function() {
  const k = $("#sk").value.trim();
  const v = $("#sv").value;
  if (!k) { toast("Key required", "error"); return; }
  await api("/settings", { method: "PUT", body: JSON.stringify({ key: k, value: v }) });
  toast("Saved", "success");
  navigate();
};

window.deleteSetting = async function(key) {
  await api(`/settings/${encodeURIComponent(key)}`, { method: "DELETE" });
  toast("Deleted", "success");
  navigate();
};

// ============================================================
// Bootstrap
// ============================================================

document.addEventListener("DOMContentLoaded", navigate);
if (document.readyState !== "loading") navigate();
