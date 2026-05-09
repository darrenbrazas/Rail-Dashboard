let lifecycle = {
  requirements: [],
  changes: [],
  baselines: [],
  testRuns: [],
  zones: {},
  kpis: [],
  metrics: {},
  simulation: { summary: "Simulation evidence is unavailable.", scenarios: [] },
};
let integrations = { jira: { configured: false, dryRun: true } };

const statusClass = {
  Verified: "verified",
  "In Review": "review",
  Failed: "failed",
  "Not Started": "started",
};

function renderRequirements(filter = "all") {
  const table = document.querySelector("#requirementsTable");
  const rows = lifecycle.requirements
    .filter((item) => filter === "all" || item.status === filter)
    .map(
      (item) => `
        <tr>
          <td><strong>${item.id}</strong></td>
          <td>${item.text}</td>
          <td>${item.config}</td>
          <td>${item.test}</td>
          <td><span class="status ${statusClass[item.status]}">${item.status}</span></td>
        </tr>
      `,
    )
    .join("");

  table.innerHTML = rows;
  renderRequirementOptions();
}

function renderRequirementOptions() {
  const select = document.querySelector("#changeRequirementSelect");
  if (!select) {
    return;
  }
  select.innerHTML = lifecycle.requirements
    .map((item) => `<option value="${item.id}">${item.id}</option>`)
    .join("");
}

function renderChanges() {
  document.querySelector("#changeBoard").innerHTML = lifecycle.changes
    .map(
      (item) => `
        <article class="ticket">
          <strong>${item.id}: ${item.title}</strong>
          <span class="tag ${item.priority === "Critical" ? "bad" : item.priority === "High" ? "warn" : "good"}">${item.priority}</span>
          <div class="meta">
            <span>Owner: ${item.owner}</span>
            <span>Requirement: ${item.requirement}</span>
            <span>Status: ${item.status}</span>
            <span>Jira: ${item.jira_sync_status || "Not Synced"}</span>
          </div>
          <div class="ticket-actions">
            <button type="button" data-sync-jira="${item.id}">Sync Jira</button>
            ${
              item.jira_url
                ? `<a href="${item.jira_url}" target="_blank" rel="noreferrer">${item.jira_key}</a>`
                : "<span>No Jira key yet</span>"
            }
          </div>
        </article>
      `,
    )
    .join("");
  document.querySelectorAll("[data-sync-jira]").forEach((button) => {
    button.addEventListener("click", async () => {
      await postJson(`/api/changes/${button.dataset.syncJira}/sync-jira`, {});
      await refreshLifecycle();
    });
  });
}

function renderBaselines() {
  document.querySelector("#baselineList").innerHTML = lifecycle.baselines
    .map(
      (item) => `
        <article class="baseline">
          <strong>${item.name}</strong>
          <p>${item.scope}</p>
          <span class="tag ${item.risk}">${item.status}</span>
        </article>
      `,
    )
    .join("");
}

function renderTests() {
  document.querySelector("#testRuns").innerHTML = lifecycle.testRuns
    .map((run) => {
      const total = run.passed + run.failed;
      const rate = Math.round((run.passed / total) * 100);
      return `
        <article class="test-run">
          <strong>${run.id}</strong>
          <p>${run.suite}</p>
          <div class="bar-row">
            <div class="bar-label"><span>${run.passed} passed / ${run.failed} failed</span><span>${rate}%</span></div>
            <div class="bar-track"><div class="bar-fill" style="width: ${rate}%"></div></div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderSimulation() {
  document.querySelector("#simulationSummary").textContent = lifecycle.simulation.summary;
  document.querySelector("#simulationRuns").innerHTML = lifecycle.simulation.scenarios
    .map((scenario) => {
      const resultClass = scenario.result === "PASS" ? "good" : "bad";
      return `
        <article class="test-run">
          <strong>${scenario.id} - Zone ${scenario.zone}</strong>
          <p>${scenario.speedKmh} km/h, safe limit ${scenario.safeLimitMeters} m, computed ${scenario.computedDistanceMeters} m</p>
          <span class="tag ${resultClass}">${scenario.result}</span>
        </article>
      `;
    })
    .join("");
}

function renderZone(zoneId = "A") {
  const zone = lifecycle.zones[zoneId];
  document.querySelector("#zoneDetails").innerHTML = `
    <h4>${zone.title}</h4>
    <p>${zone.details}</p>
  `;
}

function renderKpis() {
  document.querySelector("#kpiBars").innerHTML = lifecycle.kpis
    .map(
      ([label, value]) => `
        <div class="bar-row">
          <div class="bar-label"><span>${label}</span><span>${value}%</span></div>
          <div class="bar-track"><div class="bar-fill" style="width: ${value}%"></div></div>
        </div>
      `,
    )
    .join("");
}

function renderMetrics() {
  document.querySelector("#verifiedMetric").textContent = `${lifecycle.metrics.requirementsVerified}%`;
  document.querySelector("#openChangesMetric").textContent = lifecycle.metrics.openChanges;
  document.querySelector("#buildHealthMetric").textContent = `${lifecycle.metrics.buildHealth}%`;
  document.querySelector("#procurementMetric").textContent = lifecycle.metrics.procurementRisk;
}

function exportReport() {
  const report = [
    "Rail Lifecycle Control Center - Portfolio Report",
    "",
    `Requirements verified: ${document.querySelector("#verifiedMetric").textContent}`,
    `Open change requests: ${lifecycle.changes.length}`,
    `Build health: ${document.querySelector("#buildHealthMetric").textContent}`,
    "",
    "Top risks:",
    ...lifecycle.changes.map((item) => `- ${item.id}: ${item.title} (${item.status})`),
  ].join("\n");

  const blob = new Blob([report], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "rail-lifecycle-report.txt";
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportCsv() {
  window.location.href = "/api/export/traceability.csv";
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

function formPayload(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function refreshLifecycle() {
  lifecycle = await loadLifecycle();
  renderAll();
}

async function loadLifecycle() {
  const response = await fetch("/api/lifecycle");
  if (!response.ok) {
    throw new Error("Unable to load lifecycle API");
  }
  return response.json();
}

async function loadIntegrations() {
  const response = await fetch("/api/integrations");
  if (!response.ok) {
    throw new Error("Unable to load integration status");
  }
  return response.json();
}

function renderIntegrations() {
  const status = document.querySelector("#jiraStatus");
  const jira = integrations.jira;
  if (jira.configured && !jira.dryRun) {
    status.textContent = `Jira: live ${jira.projectKey}`;
    return;
  }
  if (jira.dryRun) {
    status.textContent = `Jira: dry run ${jira.projectKey || "RAIL"}`;
    return;
  }
  status.textContent = "Jira: not configured";
}

function renderAll() {
  renderRequirements();
  renderChanges();
  renderBaselines();
  renderTests();
  renderSimulation();
  renderZone();
  renderKpis();
  renderMetrics();
  renderIntegrations();
}

document.addEventListener("DOMContentLoaded", async () => {
  lifecycle = await loadLifecycle();
  integrations = await loadIntegrations();
  renderAll();

  document.querySelector("#requirementFilter").addEventListener("change", (event) => {
    renderRequirements(event.target.value);
  });

  document.querySelector("#exportReport").addEventListener("click", exportReport);
  document.querySelector("#exportCsv").addEventListener("click", exportCsv);

  document.querySelector("#toggleTheme").addEventListener("click", () => {
    document.body.classList.toggle("high-contrast");
  });

  document.querySelectorAll(".station").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".station").forEach((station) => station.classList.remove("active"));
      button.classList.add("active");
      renderZone(button.dataset.zone);
    });
  });

  document.querySelector("#requirementForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await postJson("/api/requirements", formPayload(event.target));
    event.target.reset();
    await refreshLifecycle();
  });

  document.querySelector("#changeForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await postJson("/api/changes", formPayload(event.target));
    event.target.reset();
    await refreshLifecycle();
  });
});
