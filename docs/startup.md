# ControlPlane.ai Startup Guide

This guide provides instructions on how to start the ControlPlane.ai project from scratch. It includes a specific set of instructions for your current local setup (Windows, Python, Node), as well as a generic method using Docker.

---

## Method 1: Local Development (Native on Your Computer)

This is the fastest method for local development, leveraging your currently installed software. In this mode, the backend automatically falls back to an in-memory SQLite database, so you do not need PostgreSQL or Redis running.

### 1. Setup the Environment

Make sure you have your `.env` file set up in the root or `backend` folder.
```powershell
cp .env.example .env
```
*(Optionally edit `.env` to include your `OPENAI_API_KEY` if you want real LLM generations instead of fallbacks).*

### 2. Start the Backend (FastAPI)

Open a PowerShell terminal and run:

```powershell
cd backend

# Install dependencies (if you haven't already)
pip install -r requirements.txt

# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see logs indicating that the tables are created and demo data is seeded. 
- API URL: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`

### 3. Start the Frontend (React + Vite)

Open a **new** PowerShell terminal and run:

```powershell
cd frontend

# Install Node modules (if you haven't already)
npm install

# Start the Vite dev server
npm run dev
```

- Control Room Dashboard: `http://localhost:3000`

---

## Method 2: Generic Setup (Using Docker Compose)

This is the recommended approach for running the system on any machine without needing to install Python, Node, or set up local databases manually. It will spin up the backend, frontend, PostgreSQL (with pgvector), and Redis.

### 1. Setup the Environment

```bash
cp .env.example .env
```
Ensure your `.env` file contains the correct `DATABASE_URL` pointing to PostgreSQL:
```ini
DATABASE_URL=postgresql+asyncpg://controlplane:controlplane@postgres:5432/controlplane
SYNC_DATABASE_URL=postgresql://controlplane:controlplane@postgres:5432/controlplane
REDIS_URL=redis://redis:6379/0
```

### 2. Run Docker Compose

Ensure Docker (e.g., Docker Desktop) is running, then execute:

```bash
docker compose up --build -d
```

### 3. Access the Services

Once the containers are built and started, the services will be available at the same ports:
- **Frontend Dashboard:** `http://localhost:3000`
- **Backend API Docs:** `http://localhost:8000/docs`

### 4. Stopping the Services

To shut down the Docker containers:

```bash
docker compose down
```

---

## Running Demo Scenarios

Once the system is up and running (using either method above), you can test the core AI Risk evaluation engines using the built-in demo scenarios. 

Open a terminal and run the end-to-end Python script to see how the system handles different risks (Hallucinations, PII Leakage, Cost Anomalies, Escalation):

```powershell
cd backend
python test_all_scenarios.py
```

Alternatively, you can trigger individual scenarios via curl:
```powershell
curl -X POST http://localhost:8000/api/v1/demo/run/hallucination
```
