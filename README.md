# 🚀 BMR OCR Engine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4.0-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, high-performance web application designed for **OCR verification** and automated data extraction from **Batch Manufacturing Records (BMR)** and **Quality Control (QC)** reports. This system leverages advanced LLMs (Mistral AI) and robust OCR engines to ensure high accuracy and streamlined workflows in pharmaceutical and manufacturing environments.

---

## ✨ Key Features

- 🔍 **Intelligent Extraction**: Schema-native, LLM-based data extraction using Mistral AI.
- 📑 **Multi-Format Support**: Process both PDF documents and image files seamlessly.
- 🎨 **Modern UI/UX**: Stunning **Neon Glassmorphism** interface built with React 19 and Tailwind CSS 4.
- 🛠️ **Real-time Verification**: Interactive verification dashboard to review and correct extracted data.
- ⚡ **High Performance**: FastAPI backend ensuring low-latency processing and API responses.
- 📊 **Audit-Ready**: Built-in database logging and audit trails for compliance.
- 🔄 **Automated Migrations**: Easy database schema management with Alembic.

---

## 🛠️ Tech Stack

### Backend
| Technology | Description |
| :--- | :--- |
| **FastAPI** | High-performance web framework for APIs. |
| **Mistral AI** | Advanced LLM for structured data extraction. |
| **SQLAlchemy** | SQL toolkit and Object-Relational Mapper (ORM). |
| **Alembic** | Lightweight database migration tool. |
| **OpenCV / Pillow** | Image processing and manipulation. |
| **PyMuPDF (fitz)** | PDF handling and document conversion. |

### Frontend
| Technology | Description |
| :--- | :--- |
| **React 19** | The latest React core for the UI components. |
| **Vite** | Fast build tool and development server. |
| **Tailwind CSS 4** | Utility-first CSS framework for modern styling. |
| **Lucide React** | Beautifully simple pixel-perfect icons. |
| **Axios** | Promise-based HTTP client for API communication. |

---

## 🚀 Quick Start (Windows)

To run the full application locally, you will need two terminal sessions.

### 1. Backend Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py --server
```
*API will be running at: `http://localhost:8000`*

### 2. Frontend Setup
```powershell
cd ui/react-app
npm install
npm run dev
```
*UI will be accessible at: `http://localhost:5173`*

---

## 🔦 Core Commands

The `main.py` script serves as the primary entry point for various system operations:

| Command | Description |
| :--- | :--- |
| `python main.py --server` | Launch the FastAPI production-ready server. |
| `python main.py --init-db` | Initialize the SQLite database schema. |
| `python main.py --process <path>` | Process a specific PDF/Image file via CLI. |

---

## 📁 Project Structure

```text
├── .agent/              # Custom agentic workflows and AI skills
├── .vscode/             # Editor configuration and settings
├── app/                 # Backend source code (FastAPI)
│   ├── core/            # Core configuration and security
│   ├── engines/         # OCR, Classification, and Validation logic
│   ├── models/          # Database ORM models (SQLAlchemy)
│   ├── routers/         # API endpoints and route definitions
│   └── schemas/         # Pydantic data validation schemas
├── data/                # Document storage (inputs, images, uploads)
├── docs/                # Project documentation and specifications
├── field_specs/         # YAML definitions for field extraction
├── output/              # Processed results and exported data
├── templates/           # Document and export templates
├── tmp/                 # Temporary processing files
├── ui/                  # Frontend application
│   └── react-app/       # React/Vite/Tailwind source code
└── requirements.txt     # Python dependencies
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Developed with ❤️ by the BMR OCR Team.
