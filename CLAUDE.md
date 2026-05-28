# Claude Project Guide

This repository is an AI welfare recommendation and referral web service for field workers.

Last handoff update: 2026-05-29.

## Current Product State

- The app helps a case worker enter a consultation memo, structure the case, search welfare services, select or adjust a recommendation package, inspect service details, save/load consultation cases, and generate a practical recommendation report.
- The deployed Render service runs with `python server_entry.py`.
- Public welfare APIs and Gemini are configured through environment variables. Never commit API keys, Render secrets, Gemini keys, public-data keys, personal tokens, or real consultation data.
- The service is intentionally lightweight: Python standard library backend plus static frontend JavaScript and CSS.
- GitHub `main` is connected to Render auto-deploy when the Render repository connection is healthy.

## Current Active Files

- `backend_server.py`: base HTTP server, API routes, public-data calls, file-based case persistence, local fallback catalog, and core recommendation helpers.
- `server_entry.py`: production entrypoint that applies runtime patches before starting the server.
- `sitecustomize.py`: import hook that reapplies runtime patches when the base server is imported in alternate paths.
- `app.js`: main frontend state, screen rendering, API calls, package selection, detail modal, and report flow.
- `styles.css`: base UI styling.
- `age-filter-patch.js`: frontend age/target compatibility safety patch.
- `auto-package-flow-patch.js`: automatic package selection flow patch.
- `status-feedback-patch.js`: AI workflow progress/status, detail summary, and report UI patch.
- `case-loading-link-patch.js`: loading-state and official-link UI patch.
- `commercial-ui-polish.js`: commercial UI behavior layer and login/workflow visual polish.
- `commercial-ui-style-fix.js`: compatibility style layer for login preview visuals. Keep this loaded unless the CSS/JS layers are consolidated and verified on Render.
- `case-list-persistence-patch.js`: dashboard case-list UI and frontend save/load/delete integration with `/api/cases`.
- `commercial_ui_route_patch.py`: serves supplemental JavaScript files from the Python server.
- `backend_runtime_patch.py`: backend runtime compatibility and public-data behavior patch.
- `recommendation_relevance_patch.py`: consultation-aware recommendation relevance adjustments.
- `detail_alias_patch.py`: service detail identifier and alias resolution.
- `llm_enhancement_patch.py`: Gemini-backed structuring, service-detail summarization, candidate reranking, and richer report text.
- `rich_report_patch.py`: report generation enhancements.
- `welfare_link_patch.py`: official/deep-link URL improvement helpers for Bokjiro and external service portals.
- `README.md` and `TEAM_ROLES.md`: human-facing project and collaboration docs.
- `.github/workflows/claude.yml`: Claude Code Action trigger. It expects the repository secret `ANTHROPIC_API_KEY`.

## Current API Surface

- `GET /api/health`: service, public-data, and LLM status.
- `GET /api/services`: integrated welfare service search.
- `GET /api/services/{id}`: welfare service detail, summary, official link, and related providers.
- `GET /api/providers`: social-service providers, private resources, and local institution candidates.
- `GET /api/cases`: saved consultation cases.
- `GET /api/cases/recent`: backward-compatible alias for saved consultation cases.
- `POST /api/cases`: save or update a consultation case.
- `DELETE /api/cases/{id}`: delete a saved consultation case.
- `POST /api/analyze`: structure a consultation memo.
- `POST /api/packages`: generate recommendation packages.
- `POST /api/report`: generate a practical recommendation report.

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

The previous large HWP/dashboard/applicationDraft change was intentionally rolled back. Current work should treat those files and UI patterns as absent.

## Engineering Rules

- Keep changes small and task-focused.
- Prefer extending existing patch modules over broad rewrites of `backend_server.py` unless the task explicitly calls for consolidation.
- If a frontend fix is visual, verify both login and logged-in workflow screens when possible.
- For welfare-service detail data, prefer official API fields first. If a field is missing, mark fallback/template-derived information clearly.
- Avoid demo-only behavior that ignores the consultation memo. Recommendations should be tied to case needs, risks, age, region, and target type.
- Do not ask users to paste credentials into GitHub comments. Tell them to use GitHub Secrets or Render environment variables.
- Current case persistence uses `.data/cases.json` by default. Treat it as MVP storage, not production-grade persistence.

## Validation Commands

Run these when relevant:

```bash
npm run check
```

Or individually:

```bash
npm run check:js
npm run check:py
```

Equivalent explicit commands:

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
node --check case-list-persistence-patch.js
```

If Node or Python is unavailable in the runner, explain that limitation in the PR or issue response.

## Deployment Smoke Checks

After a Render deploy, check:

- `/api/health` returns `ok: true`.
- `/api/health` shows public data and LLM enabled when Render secrets are configured.
- `/case-list-persistence-patch.js` returns 200.
- `/api/cases` returns a JSON response with `cases`.
- The login page no longer shows the removed `HWP 가이드 포함` badge.
- A saved consultation appears in `상담 목록` and can be loaded again.
- Service detail URLs for external portals such as MyHome, Work24, KYCI, NHIS, and Long-term Care point to official detail/guide pages rather than only homepages when a stable page is known.
- A senior-care consultation should not surface youth-only services as top recommendations.
- The consultation flow still works: demo login -> dashboard -> consultation input -> AI structuring -> integrated search -> package recommendation -> report.

## Suggested First Tasks For Claude

Good starting issues:

- Replace `.data/cases.json` MVP persistence with SQLite, PostgreSQL, or Render Disk-backed storage.
- Consolidate `commercial-ui-polish.js`, `commercial-ui-style-fix.js`, `case-list-persistence-patch.js`, and `styles.css` after screenshot verification.
- Add automated smoke tests for the consultation flow and service-detail modal.
- Improve recommendation diversity so repeated consultations do not always produce the same package.
- Add safer service-detail fallback labeling when official APIs return no detail.
- Add 개인정보 masking for 주민등록번호, phone numbers, and detailed addresses.

## GitHub Collaboration Style

- Work on a branch for non-trivial changes.
- Keep PRs focused to one behavior area: frontend UX, backend/API, recommendation quality, or docs.
- In PR summaries, include what changed, why, how it was checked, and any remaining risks.
- If external credentials or dashboard actions are required, document the required secret name instead of exposing the value.

## How To Call Claude Code In GitHub

The workflow runs when an issue, PR comment, review comment, or issue body contains `@claude`.

Example issue comment:

```text
@claude Read CLAUDE.md first. Please fix the integrated search/package selection issue. Keep the change small, run npm run check if code changes, and summarize any Render follow-up needed.
```
