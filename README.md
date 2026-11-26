# CyberSafe Cybercrime Reporting Website

CyberSafe is a local development prototype for cybercrime reporting. It includes a Flask API, a MySQL database, and a plain HTML/CSS/JavaScript frontend.

> **Prototype notice:** Do not use this project to handle real victims' reports or evidence. The AI trend “predictions” are fixed illustrative text, not forecasts. Per-report analysis may use an external AI provider when configured and otherwise uses simple rules; its severity and confidence values are not validated for real-world decisions. Review privacy, security, legal, operational, and model requirements before any real deployment.

## Requirements

- Windows 10/11
- VS Code
- Python 3.10 or newer
- MySQL Server 8 or compatible MySQL server, running locally
- Python (the built-in HTTP server runs the frontend; no VS Code extension is required)

The backend dependencies are listed in `backend/requirements.txt`. OpenAI is optional; without an API key, the application uses its rule-based fallback.

## Run it in VS Code on Windows

### 1. Open the project

In VS Code, choose **File → Open Folder** and open the extracted `cyber-crime-reporting-website` folder. The correct folder contains `backend`, `frontend`, and `database`.

### 2. Create the database

Start MySQL. Open `backend/database/schema.sql` in MySQL Workbench and run the whole script. It creates the `cybersafe_db` database and its tables.

### 3. Configure the backend

Open a VS Code terminal (**Terminal → New Terminal**) and run:

```powershell
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run this once in that terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Edit `backend/.env` and set your local MySQL user and password. Generate three different secret values in the activated terminal:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the first two generated values in `SECRET_KEY` and `JWT_SECRET_KEY`, and the Fernet value in `DATA_ENCRYPTION_KEY`. Keep these values private and do not replace them after storing encrypted data. `OPENAI_API_KEY` is optional; leave it blank to use the rule-based report analysis. Save `.env`.

### 4. Start the backend API

Keep the terminal in the `backend` folder with `.venv` active, then run:

```powershell
python app.py
```

The API should be available at `http://127.0.0.1:5000`. Open `http://127.0.0.1:5000/health` to check that it started. Leave this terminal running. To check CORS, open another terminal in the `backend` folder and run:

```powershell
.\check_local_setup.ps1
```

### 5. Start the frontend

Open a **second VS Code terminal** and run:

```powershell
cd frontend
py -m http.server 3000
```

Open `http://localhost:3000/` in your browser. Keep both terminals running while using the site. The backend explicitly adds CORS response headers to API responses and preflight requests for the origins listed in `backend/.env`.

## Project structure

```text
backend/                 Flask API, routes, database models, and services
  database/schema.sql    MySQL schema for a new local database
  database/migrations/   SQL migrations for existing databases
  requirements.txt       Python dependencies
  .env.example           Safe template; copy to .env and configure
frontend/                Website pages, styles, scripts, and images
database/                Empty legacy placeholders; not the active schema
tests/                   Automated tests
uploads/evidences/       Local evidence uploads (not included in release ZIP)
```

## Useful notes

- Register a user through the site. Complaint submission and personal complaint tracking require sign-in.
- The app stores local database data and uploaded files on your computer. Back up the database and uploads before removing them.
- The optional AI service can send report descriptions to its configured provider. Do not submit real personal or case data to this prototype.
- Complaint status tracking is account-protected. The current public-facing tracking page does not make tracking available without signing in.
- For an existing database, review and apply any pending SQL scripts in `backend/database/migrations/` before running a newer version.
- The project is configured for local development. It is not configured for public hosting or production deployment.

## Run the AI helper unit tests

From the `backend` folder with the virtual environment active:

```powershell
$env:OPENAI_API_KEY = ''
python -m unittest discover -s ..\tests -p 'test_ai_service.py' -v
```

The crime-report tests use the configured database. Run those only against a dedicated test database, not a database containing reports you want to keep.
