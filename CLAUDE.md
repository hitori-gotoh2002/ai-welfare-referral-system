# Claude Project Guide

This repository is an AI welfare recommendation and referral web service for field workers.

## Product Context

- The app helps a case worker enter a consultation memo, structure the case, search welfare services, select a recommendation package, and generate a report with HWP application guidance.
- The deployed Render service runs with `python server_entry.py`.
- Public welfare APIs and Gemini are configured through environment variables. Never commit API keys or secrets.
- The service is intentionally lightweight: Python standard library backend plus static frontend JavaScript and CSS.

## Important Files

- `backend_server.py`: base HTTP server, API routes, public-data calls, local fallback catalog.
- `server_entry.py`: production entrypoint that applies runtime patches before starting the server.
- `app.js`: main frontend state and rendering logic.
- `styles.css`: base UI styling.
- `feature-ui.css`: dashboard, HWP guide, official link buttons, and commercial UI style layer served together with `styles.css`.
- `backend_runtime_patch.py`, `recommendation_relevance_patch.py`, `llm_enhancement_patch.py`, `rich_report_patch.py`, `welfare_feature_patch.py`, `detail_source_patch.py`: focused runtime patches. Preserve their import order unless there is a clear reason to change it.
- `README.md` and `TEAM_ROLES.md`: human-facing project and collaboration docs.

## Engineering Rules

- Keep changes small and task-focused.
- Prefer extending existing patch modules over broad rewrites of `backend_server.py` unless the task explicitly calls for consolidation.
- Do not hardcode API keys, Render secrets, Gemini keys, public-data keys, or personal tokens.
- For welfare-service detail data, prefer official API fields first. If a field is missing, mark fallback/template-derived information clearly.
- Region compatibility is important. Do not recommend a local-government service outside the resident's region.
- Avoid demo-only behavior that ignores the consultation memo. Recommendations should be tied to case needs, risks, age, region, and target type.

## Validation Commands

Run these when relevant:

```bash
python -m py_compile backend_server.py backend_runtime_patch.py recommendation_relevance_patch.py detail_alias_patch.py llm_enhancement_patch.py rich_report_patch.py welfare_link_patch.py welfare_feature_patch.py commercial_ui_route_patch.py detail_source_patch.py server_entry.py sitecustomize.py
```

```bash
node --check app.js
node --check age-filter-patch.js
node --check auto-package-flow-patch.js
node --check status-feedback-patch.js
node --check case-loading-link-patch.js
node --check dashboard-hwp-patch.js
node --check commercial-ui-polish.js
```

If Node is unavailable in the runner, explain that limitation in the PR or issue response.

## Deployment Notes

- Render auto-deploys from the GitHub `main` branch when connected.
- Health check endpoint: `/api/health`.
- Useful smoke checks after deployment:
  - `/styles.css` should include `case-dashboard-table` and `hwp-guide-card`.
  - `/api/health` should show public data and LLM enabled when secrets are configured.
  - A report generated for a Gyeonggi resident should not include Seoul-only local services.

## Collaboration Style

- When responding on GitHub, summarize what changed, why, and how it was checked.
- If a request touches product behavior, mention user impact in plain language.
- If external credentials or dashboard actions are required, do not ask the user to paste keys into comments. Tell them to add the value through GitHub Secrets or Render environment variables.
