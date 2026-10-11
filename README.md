# Bulk Certificate Generator — Backend Assignment

A high-performance, production-minded FastAPI backend system designed for bulk certificate generation with an interactive **Minimal Studio Frontend**. The system accepts bulk generation requests, independently validates recipient records, renders landscape A4 PDF certificates using ReportLab, persists jobs and certificate metadata in MySQL (with full SQLAlchemy 2.x ORM support and SQLite test isolation), isolates failures so valid recipients continue processing, and provides streaming download endpoints with directory traversal protection.

---

## 1. Problem Statement
Educational institutions, conferences, and bootcamps regularly issue certificates to hundreds of attendees. Traditional manual certificate generation is error-prone and time-consuming. In bulk systems, three common flaws frequently arise:
1. **Fragile Batch Processing**: A typo in a single recipient's email halts the entire batch of 500 recipients.
2. **Insecure Storage & Access**: Certificates are exposed via predictable identifiers or unsafe filesystem paths.
3. **Black-box Progress**: Clients lack visibility into individual recipient outcomes, failure reasons, and batch progress.

This project solves these issues with a resilient bulk generation engine, deterministic per-recipient failure isolation, secure UUID-based storage, full RESTful transparency, and an interactive browser dashboard.

---

## 2. Features
- **Minimal Studio Frontend**: Built with pure HTML/CSS/Vanilla JS, served directly at `http://localhost:8000/`. Lets you interactively add recipients, load realistic test batches, submit generation jobs, observe progress bars, and download generated certificates.
- **Bulk Job Processing**: Submit up to 500 recipients per batch with event and certificate metadata.
- **Independent Recipient Validation**: Request-level structural checks reject malformed batches immediately, while recipient-level semantic checks (empty names, invalid email syntax) allow valid recipients in the same batch to succeed.
- **Fail-Safe Generation Loop**: Utilizes database savepoints to isolate PDF generation crashes; subsequent recipients are processed without data corruption.
- **Professional PDF Engine**: Native ReportLab certificate generation featuring landscape A4 layout, double borders, corner flourishes, verified seal badge, prominent recipient typography, and customizable body text.
- **Relational Persistence**: Built with SQLAlchemy 2.x supporting **MySQL** (via `pymysql` with production connection pooling) and SQLite.
- **Secure Document Delivery**: Stream certificates directly via `/api/certificates/{certificate_id}/` with strict path traversal boundaries and safe download filenames.
- **Granular Status & Pagination**: Retrieve jobs with dynamic progress percentage and paginate recipient results with optional status filters (`SUCCESS`, `FAILED`, `PENDING`).
- **Comprehensive Automated Testing**: 16 automated pytest tests covering creation, validation, individual failures, PDF generation, security boundaries, and frontend serving.

---

## 3. Technology Stack
- **Language**: Python 3.11+
- **Backend Framework**: FastAPI (v0.110+)
- **Frontend**: Minimal Studio (Vanilla HTML5, CSS3, ES6 JavaScript)
- **Database**: MySQL 8.x (with SQLite support for tests)
- **Database Driver**: PyMySQL + Cryptography
- **ORM**: SQLAlchemy 2.x (Declarative Base, Mapped Columns, Savepoints)
- **Data Validation & Settings**: Pydantic v2 & Pydantic-Settings
- **PDF Generation**: ReportLab 4.x
- **Testing**: Pytest & FastAPI TestClient (HTTPX)
- **ASGI Server**: Uvicorn

---

## 4. Architecture and Project Structure

```
Bulk Certificate_Generator_Backend_Assignment/
├── app/
│   ├── __init__.py                 # Application package marker
│   ├── main.py                     # FastAPI application setup, lifecycle, static mounts, and middleware
│   ├── config.py                   # Pydantic Settings and environment configuration
│   ├── database.py                 # SQLAlchemy 2.x engine, connection pool, and session
│   ├── models.py                   # Relational ORM models (GenerationJob, Recipient, Certificate)
│   ├── schemas.py                  # Pydantic request and response schemas
│   ├── api/
│   │   ├── __init__.py             # Consolidated API router
│   │   ├── jobs.py                 # POST /api/jobs/, GET /api/jobs/{id}/, GET /api/jobs/{id}/recipients/
│   │   ├── recipients.py           # GET /api/recipients/{id}/
│   │   └── certificates.py         # GET /api/certificates/{id}/ (PDF download)
│   ├── services/
│   │   ├── __init__.py             # Service package marker
│   │   ├── job_service.py          # Bulk job orchestration, progress, and pagination
│   │   └── certificate_service.py  # Recipient validation, PDF triggering, and path security
│   └── utils/
│       ├── __init__.py             # Utilities package marker
│       └── pdf_generator.py        # ReportLab vector certificate rendering
├── static/
│   ├── index.html                  # Minimal studio single-page interface
│   ├── style.css                   # Custom modern design system
│   └── app.js                      # Dynamic client logic and PDF download triggers
├── storage/
│   └── certificates/               # Directory for generated PDF files
├── tests/
│   ├── __init__.py                 # Test package marker
│   ├── conftest.py                 # Pytest fixtures (isolated DB & storage)
│   ├── test_jobs.py                # Job creation, status retrieval, and pagination tests
│   ├── test_validation.py          # Request-level validation and batch limit tests
│   ├── test_certificates.py        # PDF generation, download, frontend, and security boundary tests
│   └── test_failures.py            # Simulated PDF crashes & failure isolation tests
├── .env                            # Active environment configuration
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
├── init_db.py                      # Database setup helper script
├── requirements.txt                # Production and development dependencies
├── run.py                          # Local server launcher
└── README.md                       # Complete documentation
```

---

## 5. Prerequisites
- **Python**: 3.11 or higher
- **MySQL**: 8.0+ running on port 3306 (or SQLite if MySQL is not installed)

---

## 6. Installation & Execution Steps (Windows PowerShell / CMD)

### Step 1: Navigate to the Workspace Directory
```powershell
cd "c:\Aero\Bulk Certificate_Generator_Backend_Assignment"
```

### Step 2: Create & Activate Virtual Environment
If creating the virtual environment from scratch:
```powershell
# Using Python to create .venv:
python -m venv .venv
```
*(If `python` is not in your global PATH on Windows, locate your Python binary, e.g. `& "$env:LOCALAPPDATA\Python\bin\python.exe" -m venv .venv`)*

**Activate the virtual environment**:
- **Windows (PowerShell)**:
  ```powershell
  # If PowerShell blocks script execution, run this once:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt / CMD)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

*(Once activated, your terminal prompt will show `(.venv)` at the beginning).*

---

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure the Environment (`.env`)
Create `.env` from `.env.example`:
```powershell
# PowerShell:
Copy-Item .env.example .env

# CMD:
copy .env.example .env
```

Open [.env](file:///c:/Aero/Bulk%20Certificate_Generator_Backend_Assignment/.env) and ensure your MySQL root password is set:
```ini
# Application Metadata
APP_NAME="Bulk Certificate Generator"
APP_ENV="development"
DEBUG=True

# Server Host & Port
HOST="0.0.0.0"
PORT=8000

# Database Configuration (MySQL)
DATABASE_URL="mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/bulk_certificates_db?charset=utf8mb4"

# Local Storage Directory
STORAGE_DIR="storage/certificates"
MAX_BATCH_SIZE=500
```

---

### Step 5: Initialize the MySQL Database & Tables
Create the `bulk_certificates_db` schema and tables in MySQL Workbench:

- **Method A (One-click / batch)**:
  ```powershell
  .\create_tables.bat
  ```
- **Method B (Using activated venv)**:
  ```powershell
  python init_db.py
  ```
- **Method C (Directly via venv path)**:
  ```powershell
  .\.venv\Scripts\python.exe init_db.py
  ```
- **Method D (In MySQL Workbench)**:
  Open [schema.sql](file:///c:/Aero/Bulk%20Certificate_Generator_Backend_Assignment/schema.sql) in MySQL Workbench and click the ⚡ **Execute** button.

---

### Step 6: Start the Server
- **Method A (One-click batch)**:
  ```powershell
  .\run_app.bat
  ```
- **Method B (Using activated venv)**:
  ```powershell
  python run.py
  ```
- **Method C (Directly via venv path)**:
  ```powershell
  .\.venv\Scripts\python.exe run.py
  ```

---

### Step 7: Open the Application in Your Browser
- 🎨 **Minimal Studio Web Interface**: 👉 **[http://localhost:8000/](http://localhost:8000/)**
- 📄 **Interactive Swagger API Docs**: 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 7. Automated Testing Suite

Run the full automated test suite:
```powershell
pytest -v
```

**Result**: 16 passed tests covering all endpoints, security boundaries, edge cases, and failure modes.
