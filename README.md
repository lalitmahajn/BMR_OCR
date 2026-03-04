# BMR OCR Engine

This project is a modern web application for OCR verification, designed to extract and verify data from Batch Manufacturing Records (BMR) and Quality Control (QC) reports.

It is built with a Python (FastAPI) backend and a React (Vite) frontend.

## 🏗️ Project Structure
- `app/`: Python backend source code (FastAPI, SQLAlchemy, Extraction Engine)
- `scripts/`: Python utility scripts for ingestion, extraction dumping, and debugging
- `templates/`: JSON schema templates defining field extraction rules
- `ui/react-app/`: Modern React frontend application

---

## 🚀 Quick Start (Windows)
We have provided a unified PowerShell script to start everything automatically.

From the root directory, run:
```powershell
.\run.ps1
```
This will open two new terminal windows—one for the FastAPI backend and one for the React frontend.

To process a new document and start the servers at the same time:
```powershell
.\run.ps1 -Process "path/to/document.pdf"
```

---

## 🛠️ Manual Setup & Run

If you prefer to start components manually, follow these steps.

### Prerequisites
- **Python 3.11+**
- **Node.js** (v18+ recommended)
- **Git**

---

### Step 1: Backend Setup & Run

The backend handles the OCR extraction logic, database interactions, and exposes the REST API to the frontend.

1. **Open a terminal** in the root directory (`BMR_OCR2`).

2. **Create and activate a virtual environment:**
   ```powershell
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   *Initializes SQLite database tables defined in `app/models/domain.py`*
   ```powershell
   python main.py --init-db
   ```

5. **Process a Document:**
   *To ingest and extract data from a new PDF or image:*
   ```powershell
   python main.py --process path/to/document.pdf
   ```

6. **Start the FastAPI Backend Server:**
   ```powershell
   python main.py --server
   ```
   *The API will be available at `http://localhost:8000`*

---

### Step 2: Frontend Setup & Run

The frontend is a React application that provides a modern user interface to interact with the OCR pipeline and verify results.

1. **Open a SECOND terminal** and navigate to the frontend directory:
   ```powershell
   cd ui/react-app
   ```

2. **Install JavaScript dependencies:**
   ```powershell
   npm install
   ```

3. **Start the React Development Server:**
   ```powershell
   npm run dev
   ```
   *The UI will be accessible at `http://localhost:5173`. API requests are automatically proxied to the backend.*

---

## 🛠️ Common Workflows

### Re-running Extraction Logic
If you modify a JSON template in `templates/` (e.g., `qc_report.json`), you can test the extraction engine against existing documents in the database without re-uploading the PDF.

1. Force re-extract a specific page (e.g., Page 1):
   ```powershell
   .venv\Scripts\python.exe scripts/force_reextract_page1.py
   ```
2. Dump the updated extraction results to a text file for quick verification:
   ```powershell
   .venv\Scripts\python.exe scripts/dump_extraction_results.py
   ```
   *Check `extraction_results.txt` for the current OCR output.*

### Database Migration (Alembic)
If you modify database models in `app/models/`, apply changes using Alembic:
```powershell
alembic revision --autogenerate -m "Describe your change"
alembic upgrade head
```
