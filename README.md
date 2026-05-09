# Rail Lifecycle Control Center

The project demonstrates a rail engineering lifecycle workflow: requirements are traced to configuration items and tests, change requests are tracked through a Jira-ready workflow, controlled baselines are monitored, CI/CD-style evidence is generated, and a C++ braking simulation feeds results into a Python-backed dashboard.

Current integration status: this version includes a Jira Cloud integration layer with safe dry-run mode, local SQLite persistence, and CSV export for DOORS-compatible requirements exchange. Live Jira issue creation is enabled by adding your own Atlassian credentials in `.env`. Real IBM DOORS / DOORS Next integration still requires access to an IBM Engineering Lifecycle Management server.


## Tech Stack

- HTML, CSS, and JavaScript frontend dashboard
- Python standard-library backend API
- SQLite-backed persistence seeded from JSON lifecycle data
- Jira Cloud REST API adapter using Python standard-library HTTP tooling
- C++ braking distance simulation
- PowerShell pipeline script
- Python `unittest` validation checks
- GitHub Actions CI workflow

No third-party packages are required.

## Real Jira / DOORS Integration Status

This project is currently a local lifecycle tool with a Jira integration adapter. It can run safely without credentials in dry-run mode, or create real Jira Cloud issues once credentials are provided.

### Jira

Jira Cloud integration is implemented with two modes:

- **Dry-run mode:** generates predictable Jira-style issue keys and URLs without calling Atlassian.
- **Live mode:** creates real Jira Cloud issues through Atlassian's REST API after you provide credentials.

The integration can:

- create Jira issues from local change requests
- store the returned or dry-run Jira issue key, such as `RAIL-12`
- link dashboard change requests to the Jira ticket URL
- show Jira sync status in the dashboard

To enable live Jira, create a local `.env` file using `.env.example`:

```text
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=RAIL
JIRA_ISSUE_TYPE=Task
JIRA_DRY_RUN=true
```

Set `JIRA_DRY_RUN=false` only after the Jira site URL, email, API token, project key, and issue type are correct. Do not commit `.env` or API tokens to GitHub.

### DOORS / DOORS Next

Real IBM DOORS or DOORS Next integration usually requires access to an enterprise IBM Engineering Lifecycle Management server. Without that account/server, the practical portfolio approach is:

- export the requirements traceability matrix as CSV
- structure requirements with IDs, text, linked configuration items, linked tests, and verification status
- later upgrade to DOORS Next OSLC integration if real server access becomes available

Safe resume wording without live Jira credentials:

> Built a rail lifecycle management system with DOORS-compatible requirements export and Jira-ready change control using a Jira Cloud REST API adapter with dry-run support.

Do not claim the project is connected to a live Jira or DOORS instance until you configure credentials and demonstrate live sync.

## Features

- Responsive lifecycle dashboard.
- Requirements traceability matrix with status filtering.
- Jira-ready issue and change board.
- Dry-run/live Jira sync action for change requests.
- Create forms for new requirements and change requests.
- Configuration baseline cards with release risk state.
- CI/CD fitness testing panel with pass-rate bars.
- C++ braking simulation evidence displayed in the dashboard.
- Interactive guideway zone map.
- KPI snapshot for management reporting.
- Text report export for audit/interview demonstration.
- CSV export for the traceability matrix.
- High-contrast toggle.

## How To Run

From the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1
```

This will:

- compile the C++ braking model
- generate `generated/simulation-results.json`
- run Python lifecycle tests
- initialize the app database when the server starts

Then start the Python API and dashboard:

```powershell
python backend/server.py
```

Open:

```text
http://127.0.0.1:8080/index.html
```

Health check:

```text
http://127.0.0.1:8080/api/health
```

Lifecycle API:

```text
http://127.0.0.1:8080/api/lifecycle
```

Integration status API:

```text
http://127.0.0.1:8080/api/integrations
```

Traceability CSV:

```text
http://127.0.0.1:8080/api/export/traceability.csv
```

## Suggested Resume Bullet

Built a rail lifecycle management system using Python, SQLite, C++, JavaScript, and JSON to support DOORS-compatible requirements export, Jira-ready change control with a Jira Cloud REST API adapter, configuration baselines, CI/CD test metrics, braking simulation evidence, guideway data, CSV reporting, and KPI dashboards for safety-critical software workflows.

## Suggested Interview Explanation

I noticed that Hitachi Rail's internship postings repeatedly mention configuration management, requirements traceability, CI/CD testing, dashboards, documentation, issue tracking, systems design, and cross-functional engineering workflows. I built this project to show both the workflow and the technical side: a Python API persists lifecycle data in SQLite, a C++ program generates braking simulation evidence, automated tests validate traceability rules, and the dashboard presents the data for engineering and management review. The Jira adapter supports dry-run mode by default and can create live Jira Cloud issues when credentials are configured; requirements can be exported in a DOORS-compatible CSV format.

## Manual Steps For You

1. Run the pipeline command above.
2. Start the server with `python backend/server.py`.
3. Open the dashboard at `http://127.0.0.1:8080/index.html`.
4. Add one sample requirement and one change request in the dashboard.
5. Click `Sync Jira` on a change request. In dry-run mode, it will generate a Jira-style key without using credentials.
6. Export the traceability CSV and report.
7. Take screenshots for your GitHub README, portfolio, or application.
8. Create a GitHub repository and push the project.
9. Add the resume bullet only after you can explain the project clearly.
10. Optional but recommended: record a short demo video showing the dashboard, API endpoint, C++ simulation output, test run, and Jira dry-run sync.

## Project Structure

```text
.
+-- backend/
|   +-- config.py
|   +-- jira_client.py
|   +-- server.py
|   +-- store.py
+-- data/
|   +-- lifecycle.json
+-- scripts/
|   +-- run_pipeline.ps1
+-- simulation/
|   +-- braking_model.cpp
+-- tests/
|   +-- test_jira_client.py
|   +-- test_lifecycle.py
|   +-- test_store.py
+-- .env.example
+-- app.js
+-- index.html
+-- styles.css
+-- README.md
```

## Next Improvements

- Test live Jira Cloud issue creation with a real Atlassian project and API token.
- Add Jira status sync from live issue workflow transitions.
- Add CSV import for DOORS/DOORS Next round-trip style requirements updates.
- Add optional DOORS Next OSLC integration if an IBM ELM server is available.
- Add CSV export for procurement records and test evidence.
- Add role views for Configuration Manager, Software Engineer, Systems Designer, and Procurement Analyst.
