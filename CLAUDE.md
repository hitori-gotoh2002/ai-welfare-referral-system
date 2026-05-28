# Claude Project Guide

This repository is an AI welfare recommendation and referral web service for field workers.

Last handoff update: 2026-05-28.

## Current Product State

- The app helps a case worker enter a consultation memo, structure the case, search welfare services, select or adjust a recommendation package, inspect service details, and generate a practical recommendation report.
- The deployed Render service runs with `python server_entry.py`.
- Public welfare APIs and Gemini are configured through environment variables. Never commit API keys, Render secrets, Gemini keys, public-data keys, or personal tokens.
- The service is intentionally lightweight: Python standard library backend plus static frontend JavaScript and CSS.
- GitHub `main` is connected to Render auto-deploy when the Render repository connection is healthy.

## Current Active Files

- `backend_server.py`: base HTTP server, API routes, public-data calls, local fallback catalog, and core recommendation helpers.
- `server_entry.py`: production entrypoint that applies runtime patches before starting the server.
- `sitecustomize.py`: import hook that reapplies runtime patches when the base server is imported in alternate paths.
- `app.js`: main frontend state, screen rendering, API calls, package selection, detail modal, and report flow.
- `styles.css`: base UI styling.
- `commercial-ui-polish.js`: commercial UI behavior layer and broad visual polish.
- `commercial-ui-style-fix.js`: compatibility style layer for the login preview and dashboard case summary strip. Keep this loaded unless `commercial-ui-polish.js` and `styles.css` are fully consolidated and verified on Render.
- `commercial_ui_route_patch.py`: serves the commercial UI JavaScript files from the Python server.
- `backend_runtime_patch.py`: backend runtime compatibility and API behavior patch.
- `recommendation_relevance_patch.py`: consultation-aware recommendation relevance adjustments.
- `detail_alias_patch.py`: service detail identifier and alias resolution.
- `llm_enhancement_patch.py`: Gemini-backed structuring, service-detail summarization, candidate reranking, and richer report text.
- `rich_report_patch.py`: report generation enhancements.
- `welfare_link_patch.py`: official/deep-link URL improvement helpers.
- `README.md` and `TEAM_ROLES.md`: human-facing project and collaboration docs.
- `.github/workflows/claude.yml`: Claude Code Action trigger. It expects the repository secret `ANTHROPIC_API_KEY`.

## Rolled Back Files And Features

Do not reintroduce the following files or assumptions unless the user explicitly asks for that feature set again:

- `feature-ui.css`
- `welfare_feature_patch.py`
- `detail_source_patch.py`
- `dashboard-hwp-patch.js`
- HWP guide card UI
- applicationDraft engine
- strict region-compatibility feature patch
- dashboard table/milestone feature patch

The previous large HWP/dashboard/applicationDraft change was intentionally rolled back. Current Claude work should treat those files as absent.

## Engineering Rules

- Keep changes small and task-focused.
- Prefer extending existing patch modules over broad rewrites of `backend_server.py` unless the task explicitly calls for consolidation.
- If a frontend fix is visual, verify both login and logged-in workflow screens when possible.
- For welfare-service detail data, prefer official API fields first. If a field is missing, mark fallback/template-derived information clearly.
- Avoid demo-only behavior that ignores the consultation memo. Recommendations should be tied to case needs, risks, age, region, and target type.
- Do not ask users to paste credentials into GitHub comments. Tell them to use GitHub Secrets or Render environment variables.

## Validation Commands

Run these when relevant:

```bash
python -m py_compile backend_server.py backend_runtime_patch.py recommendation_relevance_patch.py detail_alias_patch.py llm_enhancement_patch.py rich_report_patch.py welfare_link_patch.py commercial_ui_route_patch.py server_entry.py sitecustomize.py
```

```bash
node --check app.js
node --check age-filter-patch.js
node --check auto-package-flow-patch.js
node --check status-feedback-patch.js
node --check case-loading-link-patch.js
node --check commercial-ui-polish.js
node --check commercial-ui-style-fix.js
```

If Node or Python is unavailable in the runner, explain that limitation in the PR or issue response.

## Deployment Smoke Checks

After a Render deploy, check:

- `/api/health` returns `ok: true`.
- `/api/health` shows public data and LLM enabled when Render secrets are configured.
- `/` loads both `commercial-ui-polish.js` and `commercial-ui-style-fix.js`.
- `/commercial-ui-style-fix.js` returns 200 and contains `login-product-preview` and `case-context-strip`.
- `/styles.css` should not depend on rolled-back selectors such as `case-dashboard-table` or `hwp-guide-card`.
- A senior-care consultation should not surface youth-only services as top recommendations.
- The consultation flow still works: login demo -> dashboard -> consultation input -> AI structuring -> integrated search -> package recommendation -> report.

## Suggested First Tasks For Claude

Good starting issues:

- Consolidate `commercial-ui-polish.js`, `commercial-ui-style-fix.js`, and `styles.css` after screenshot verification.
- Add automated smoke tests for the consultation flow and service-detail modal.
- Improve recommendation diversity so repeated consultations do not always produce the same package.
- Add safer service-detail fallback labeling when official APIs return no detail.
- Prepare a real persistence layer for consultations and reports.

## GitHub Collaboration Style

- Work on a branch for non-trivial changes.
- Keep PRs focused to one behavior area: frontend UX, backend/API, recommendation quality, or docs.
- In PR summaries, include what changed, why, how it was checked, and any remaining risks.
- If external credentials or dashboard actions are required, document the required secret name instead of exposing the value.

## How To Call Claude Code In GitHub

The workflow runs when an issue, PR comment, review comment, or issue body contains `@claude`.

Example issue comment:

```text
@claude Read CLAUDE.md first. Please fix the integrated search/package selection issue. Keep the change small, run the validation commands that apply, and summarize any Render follow-up needed.
```
