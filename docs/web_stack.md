# Web Stack & Development Guide

This project is a modern web application for OCR verification, built with a Python backend and a React frontend.

## 🏗️ Tech Stack

### Backend (API)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python API)
- **Language**: Python 3.11+
- **Database**: SQLite (via SQLAlchemy & Alembic)
- **Key Libraries**:
  - `uvicorn`: ASGI server
  - `pydantic`: Data validation
  - `paddleocr`: OCR engine

### Frontend (UI)
- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/) (Fast build tool)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Routing**: React Router v7
- **HTTP Client**: Axios

---

## 🚀 Development Commands

### 1. Backend Setup & Run
Run these commands from the **root directory** (`d:\Official\BMR_OCR2`).

| Action | Command | Description |
| :--- | :--- | :--- |
| **Activate Env** | `.venv\Scripts\activate` | Activate virtual environment (Windows) |
| **Install Deps** | `pip install -r requirements.txt` | Install Python dependencies |
| **Init DB** | `python main.py --init-db` | Initialize SQLite database tables |
| **Start Server** | `python main.py --server` | Start FastAPI server at `http://localhost:8000` |

### 2. Frontend Setup & Run
Run these commands from the **frontend directory** (`d:\Official\BMR_OCR2\ui\react-app`).

| Action | Command | Description |
| :--- | :--- | :--- |
| **Navigate** | `cd ui/react-app` | Go to frontend folder |
| **Install Deps** | `npm install` | Install JavaScript dependencies form `package.json` |
| **Start Dev** | `npm run dev` | Start React dev server at `http://localhost:5173` |
| **Build** | `npm run build` | Build for production |

---

## 🛠️ Common Operations

### Database Migration (Alembic)
If you modify database models in `app/models/`, run:
1. `alembic revision --autogenerate -m "Describe change"`
2. `alembic upgrade head`

### Running the Full Stack locally
You will need **two terminal windows**:

**Terminal 1 (Backend):**
```powershell
.venv\Scripts\activate
python main.py --server
```

**Terminal 2 (Frontend):**
```powershell
cd ui/react-app
npm run dev
```

Open your browser to `http://localhost:5173`. The frontend proxies API requests to the backend automatically.
