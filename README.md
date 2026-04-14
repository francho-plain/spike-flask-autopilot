# Time Tracking (Flask + CSV)

Single-page Flask app for clocking in and out.

## Features

- Mobile-first
- Two large buttons: Enter and Leave
- Time correction when clocking out (hours and minutes)
- Session list grouped by week
- Total hours per week
- No authentication
- CSV persistence
- Docker-ready

## Data structure (CSV)

File at `CSV_PATH` (default `/data/sessions.csv` in Docker):

- `id`
- `start_at` (ISO datetime in UTC)
- `end_at` (ISO datetime in UTC, empty if session is open)
- `created_at` (ISO datetime in UTC)

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://localhost:5000

## Running with Docker

```bash
docker compose up --build
```

Data is persisted in `./data/sessions.csv` on the host via the `./data:/data` volume mount, so it survives container restarts.

## Environment variables

- `TZ` (default `Europe/Madrid`)
- `CSV_PATH` (default `data/sessions.csv` locally, `/data/sessions.csv` in Docker)
- `SECRET_KEY`
- `PAGE_TITLE` (default `Time tracking`)

You can copy `.env.example` to `.env` if needed.

## Copilot in devcontainer

When the devcontainer is created or rebuilt, a strict mirror sync runs from:

- `https://github.com/francho-plain/francho-copilot` (branch `main` by default)

The following components are synced in mirror mode (additions, updates, and deletions):

- `agents/`
- `skills/`
- `instructions/`
- `prompts/`

They are placed in paths that VS Code Copilot discovers automatically:

- `.github/agents/common-*`
- `.github/skills/common-*/`
- `.github/instructions/common-*`
- `.github/prompts/common-*`

These settings coexist with the user's local VS Code/Copilot profile-level configuration. The sync only touches workspace paths inside `.github/`.

Important notes:

- Internal prompts under `.github/prompts` are not synced.
- If something is removed or changed in the upstream repo, it is removed or changed in the synced `.github/` paths on the next sync.
- User-level configuration outside the repo is never touched.
- All synced assets are prefixed with `common-` to distinguish them from local workspace configuration.
- Assets with the `common-` prefix are ignored in `.gitignore` (they should be modified in the upstream repo).

Optional variables to override the sync source/ref:

- `COPILOT_UPSTREAM_URL`
- `COPILOT_UPSTREAM_REF`

To run the sync manually:

```bash
bash .devcontainer/sync-copilot-upstream.sh
```

Or using the project Makefile target:

```bash
make copilot-sync
```
