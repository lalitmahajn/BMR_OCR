---
name: bmr-debug
description: Full stack debugging skill for BMR OCR system using Playwright, GitHub and schema-based backend.
---

# BMR OCR Engine — AI Skills & Operating Context

This file defines how the AI agent should behave when working on this project.
It prioritizes **execution, debugging workflows, and tool usage** over static explanations.

---

## 🖥️ Environment Context

* OS: Windows
* Terminal: PowerShell 7 (pwsh)
* Backend: FastAPI (Python, local server)
* Frontend: React 19 (Vite dev server)
* Database: SQLite (SQLAlchemy + Alembic)

---

## 🌐 Runtime Endpoints

### Frontend (Vite)

* Primary: http://localhost:5173/
* Network: http://192.168.2.110:5173/

### Backend (FastAPI)

* Runs on: http://0.0.0.0:8000
* Accessible via:

  * http://localhost:8000
  * http://127.0.0.1:8000
  * http://192.168.2.110:8000

### Notes

* Backend binds to all interfaces (0.0.0.0)
* Prefer `localhost` for local execution
* If browser automation fails, use network IP

---

## 🔌 Available MCP Tools

### 🎭 Playwright MCP

* Browser automation and UI inspection
* Can:

  * Open pages
  * Click / type / interact
  * Inspect DOM + CSS
  * Read console errors
  * Inspect network requests

---

## 🧠 Core System Rules

### Schema-First Extraction (CRITICAL)

* ALWAYS use Pydantic schemas (`app/schemas/`)
* NEVER use regex-based extraction
* Ensure strict mapping:

  * OCR → schema → database

---

### Extraction Pipeline Behavior

* Mistral AI performs structured extraction
* Output must strictly follow schema
* Maintain physical document page alignment
* Ensure UI receives clean, human-readable labels

---

### Database Consistency

* Schema updates MUST reflect in:

  * SQLAlchemy models (`app/models/domain.py`)
  * Alembic migrations

---

## 🎭 UI Debug Skill (Playwright MCP)

When debugging UI issues:

1. Open frontend:

   * Try http://localhost:5173
   * If fails → use http://192.168.2.110:5173

2. Navigate to relevant page

3. Reproduce issue via interaction

4. Inspect DOM and layout

5. Check CSS issues

6. Read browser console errors

7. Inspect network requests

8. For API calls:

   * Verify requests go to port 8000
   * Check for failed responses

9. Identify root cause:

   * UI bug
   * API issue
   * data/schema mismatch

10. Suggest precise fix

---

## 🎨 UI Design Validation Skill (Stitch)

When working with UI:

1. Treat Stitch as design source of truth

2. Compare implementation with design

3. Identify mismatches:

   * layout
   * spacing
   * typography
   * colors

4. Enforce Neon Glassmorphism design system

5. Suggest Tailwind CSS fixes

6. Improve component structure if needed

---

## 🔗 Backend Debug Skill (FastAPI)

When backend/API issues occur:

1. Assume backend at http://localhost:8000

2. Analyze endpoint in `app/routers/`

3. Trace request flow through:

   * routers/
   * engines/
   * schemas/

4. Validate response against schema

5. Identify processing errors

6. Suggest fixes

---

## 🧠 Schema & Extraction Skill

When working with OCR/extraction:

1. Inspect schema in `app/schemas/`
2. Ensure schema matches document structure
3. Validate mapping from OCR → schema
4. Ensure proper flattening for UI
5. Maintain page-boundary alignment
6. Suggest schema or pipeline corrections

---

## 🐙 GitHub Root Cause Skill

When issue may be caused by recent changes:

1. Use GitHub MCP to inspect commits

2. Focus on:

   * schemas
   * engines
   * UI components

3. Compare working vs broken state

4. Identify breaking change

5. Suggest fix or rollback

---

## 🔥 Full Stack Debug Skill (PRIMARY)

When issue spans multiple layers:

1. Use Playwright MCP to reproduce issue

2. Observe UI behavior

3. Inspect API requests

4. Analyze backend response

5. Validate schema + extraction pipeline

6. Compare UI with Stitch design

7. Identify root cause:

   * UI
   * API
   * schema

8. Suggest coordinated fix

---

## 🧭 Tool Usage Guidelines

* ALWAYS use Playwright MCP for UI issues
* DO NOT guess UI behavior without browser verification
* Use GitHub MCP for regressions
* Treat Stitch as design reference only
* Prefer runtime inspection over assumptions
* Correlate UI + API + schema before concluding

---

## 🌐 Network Awareness

* If localhost fails → use network IP
* Backend runs on 0.0.0.0 → accessible from multiple interfaces
* Ensure frontend ↔ backend connectivity
* Adapt URLs based on execution context

---

## ⚡ Execution Philosophy

* Do not give theoretical answers when tools can verify
* Always reproduce issues when possible
* Focus on root cause, not symptoms
* Suggest precise, code-level fixes
* Respect project architecture

---
