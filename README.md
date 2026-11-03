# TaskFlow — FastAPI + PostgreSQL + Streamlit

TaskFlow is a task manager with a FastAPI backend, PostgreSQL database, and Streamlit frontend.

## Requirements

- Python 3.10 or newer
- PostgreSQL installed and running
- A PostgreSQL database named `taskproject`
- VS Code (recommended)

## 1. Configure PostgreSQL

Make sure PostgreSQL is running locally and that the `taskproject` database exists. The project-root `.env` file contains `DATABASE_URL`; update its username, password, host, port, or database name if your local PostgreSQL setup differs. If a password contains special URL characters (such as `@`), URL-encode them (for example, `@` becomes `%40`).

The configured database user must have permission to create and modify tables in `taskproject`. The backend creates the `tasks` table automatically on startup.

## 2. Create and activate a virtual environment (Windows PowerShell)

Open a terminal in the project root and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Start the backend

From the project root, with PostgreSQL running and the virtual environment activated:

```powershell
python -m uvicorn backend.main:app --reload
```

Open these addresses:

- API status: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs
- Task list: http://127.0.0.1:8000/tasks

Keep this terminal open. If startup reports a database connection error, verify that PostgreSQL is running, the `taskproject` database exists, and `DATABASE_URL` in `.env` is correct.

## 5. Start the frontend

Open a second terminal in the project root. Activate the virtual environment in that terminal, then run:

```powershell
python -m streamlit run frontend/dashboard.py
```

Open the Streamlit address shown in the terminal (normally http://localhost:8501/). Keep both backend and frontend terminals open.

## 6. Run tests

With PostgreSQL running and `.env` configured for `taskproject`, run from the project root:

```powershell
python -m pytest -v
```

The database integration tests use the configured PostgreSQL database. The CRUD test creates and removes its own test task. The database connection test creates/uses a `connection_test` table.

## Project structure

```text
backend/
  api/routes/       FastAPI route handlers
  core/             Database configuration and session
  models/           SQLAlchemy models
  schemas/          Pydantic request/response schemas
  main.py           FastAPI application
frontend/
  components/       Reusable UI components and styling
  pages/            Streamlit page renderers
  services/         Backend API client helpers
  dashboard.py      Streamlit entry point
tests/              API and database tests
.env                Local database configuration
.gitignore
README.md
requirements.txt
```

## Troubleshooting

- **`python` is not found:** try `py` on Windows.
- **`ModuleNotFoundError`:** run commands from the project root and install `requirements.txt` in the active virtual environment.
- **PostgreSQL connection refused:** start PostgreSQL and confirm the host/port in `.env`.
- **Database does not exist:** create `taskproject` in PostgreSQL or update `DATABASE_URL` and the expected database name check in `backend/main.py` to match your intended database.
- **`psycopg2` missing:** run `python -m pip install -r requirements.txt` again.
- **Port 8000 is busy:** run `python -m uvicorn backend.main:app --reload --port 8001` and update `API_URL` in `frontend/services/api.py` to `http://127.0.0.1:8001`.

Do not commit `.env` or share it publicly; it may contain database credentials.
