# BMR OCR Engine

This project is a modern web application for OCR verification, designed to extract and verify data from Batch Manufacturing Records (BMR) and Quality Control (QC) reports.

It is built with a Python (FastAPI) backend and a React (Vite) frontend.

## 🏗️ Project Structure
- `app/`: Python backend source code (FastAPI, SQLAlchemy, Mistral AI Extraction Engine)
- `app/schemas/`: Pydantic schemas enforcing schema-native, LLM-based extraction
- `.agent/skills/`: Custom agentic workflows and AI instructions (e.g. `bmr-debug`)
- `ui/react-app/`: Modern React frontend application (Neon Glassmorphism UI)
- `*.py` (Root utility scripts): Various `tmp_*.py` and `audit_*.py` files for ingestion, database testing, and debug workflows

---

## 🚀 Quick Start (Windows)

To run the application, you will need to open two separate terminal windows.

**Terminal 1: Start the Backend (FastAPI)**
From the root directory (`BMR_OCR2`), run:
```powershell
python main.py --server
```
*(The API will be available at http://localhost:8000)*

**Terminal 2: Start the Frontend (React)**
Open a second terminal, navigate to the frontend directory, and run:
```powershell
cd ui/react-app
npm run dev
```
*(The UI will be accessible at http://localhost:5173)*

### Document Processing
To process a new document manually, run this from the root directory:
```powershell
python main.py --process "path/to/document.pdf"
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

2. **Install Python dependencies:**
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


### Database Migration (Alembic)
If you modify database models in `app/models/`, apply changes using Alembic:
```powershell
alembic revision --autogenerate -m "Describe your change"
alembic upgrade head
```
