# COMP 3613 Student Accommodation (Phase 2 starter)

Flawed baseline **0.2.0** built on [uwidcit/faststart](https://github.com/uwidcit/faststart) (`96ccfce`).

FastStart provides the SSR shell, JWT cookie auth, SQLModel, `manage.py`, and Render/Docker wiring. The student-accommodation scenario adds domain models/services and a JSON API under `/api` (see `/docs`).

## Quick start

```text
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: Copy-Item .env.example .env
python manage.py init
python manage.py run
```

Open http://127.0.0.1:5000 — SSR auth shell; scenario JSON under `/api` and OpenAPI at `/docs`.

## Seeded API accounts

| Email | Password | Role |
| --- | --- | --- |
| `admin@example.com` | `admin-dev` | admin |
| `student@example.com` | `stud-dev` | student (registered ID) |
| `incoming@example.com` | `stud-dev` | student (provisional incoming) |
| `landlord@example.com` | `land-dev` | landlord |
| `landlord2@example.com` | `land-dev` | landlord |

JSON login: `POST /api/auth/login` with `{"email","password"}`. Other scenario endpoints identify the caller with the `X-User-Id` header (demo auth).

## Student brief

See [`ASSIGNMENT.md`](ASSIGNMENT.md) and [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md).

## Tests

```bash
python -m pytest tests -q
```

## Listing lifecycle (State pattern)

A listing is always in exactly one status. Each status is a class in `app/states/` that allows only its own transitions. Anything else is refused with `409`. `ListingService` checks roles and ownership, then calls the state.

| Status | Allowed actions → new status |
| --- | --- |
| pending | approve → approved; provisionally_accept → provisional; reject → rejected; withdraw → withdrawn |
| provisional | approve → approved; reject → rejected; resubmit → pending; withdraw → withdrawn |
| approved | activate → active; force_deactivate → force_deactivated; withdraw → withdrawn |
| rejected | resubmit → pending |
| active | deactivate → inactive; force_deactivate → force_deactivated; withdraw → withdrawn |
| inactive | activate → active; withdraw → withdrawn |
| force_deactivated | resubmit → pending |
| withdrawn | none (terminal) |

Admins perform approve, provisionally_accept, reject and force_deactivate. The owning landlord performs activate, deactivate, resubmit and withdraw. Only `active` listings are visible to students.

Example (PowerShell): admin approves the seeded pending listing, then its landlord activates it.
```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/listings/2/transition -Headers @{"X-User-Id"="1"} -ContentType "application/json" -Body '{"action":"approve"}'
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/listings/2/transition -Headers @{"X-User-Id"="4"} -ContentType "application/json" -Body '{"action":"activate"}'
```

## Structure

`app/states/` (State pattern) · `app/services/` (rules and roles) · `app/repositories/` (database access) · `app/routers/` (HTTP) · `tests/`.

## Deploy

`render.yaml` is a Render Blueprint (web service plus Postgres). On start it runs `python manage.py init --no-drop` (creates tables and seeds) and then the app. Health check: `/health`.
