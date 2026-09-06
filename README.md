# ✈️ Production Flight Management & Autonomous Automation System (AeroOps OS)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Neon Postgres](https://img.shields.io/badge/Database-Neon_PostgreSQL-00E599.svg?style=flat&logo=postgresql)](https://neon.tech)
[![n8n Automation](https://img.shields.io/badge/Orchestration-n8n_Cloud-FF6D5A.svg?style=flat&logo=n8n)](https://n8n.io)
[![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-FF4F00.svg?style=flat)](https://trychroma.com)
[![Groq LLaMA-3.3](https://img.shields.io/badge/LLM-Groq_LLaMA_3.3-F55036.svg?style=flat)](https://groq.com)
[![React 19](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)

An enterprise-grade, high-concurrency **Flight Management System & Dual-Writer Automation Platform** designed to solve overselling, handle atomic inventory row-locks, autonomously manage standby waitlists, enforce dynamic fare cancellation rules, and coordinate real-time scheduled workflows.

---

## 🏛️ System Architecture

```
                               ┌───────────────────────────────────┐
                               │       React 19 + Vite UI          │
                               │   (Customer & Admin Operations)   │
                               └─────────────────┬─────────────────┘
                                                 │ HTTP / REST
                                                 ▼
                               ┌───────────────────────────────────┐
                               │         FastAPI Backend           │
                               │   (Async Row-Level Locks)         │
                               └──┬─────────────────────────────┬──┘
                                  │                             │
           Live Webhooks (POST)   │                             │ Direct AsyncPG
                                  ▼                             ▼
┌──────────────────────────────────────────────┐        ┌──────────────────────────────┐
│             n8n Cloud Engine                 │        │   Neon Serverless Postgres   │
│   (Unified Master Event Switch + Cron)       │◄───────┤   (Single Source of Truth)   │
└──────────────────────┬───────────────────────┘        └──────────────────────────────┘
                       │ Direct SQL & Gmail
                       ▼
┌──────────────────────────────────────────────┐
│  - 1. Waitlist Auto-Promotion (SKIP LOCKED)  │
│  - 2. Check-in Reminders (Suppression)       │
│  - 3. Refund SLA Escalation Alerts (>3 Days) │
│  - 4. Executive Daily Ops & Revenue Summary  │
│  - 5. Fraud Velocity Bot Scanner (>3 in 15m) │
│  - 6. Seat-Hold State Reconciliation         │
│  - 7. Live Flight Event Notifications (Gmail)│
└──────────────────────────────────────────────┘
```

---

## Some Feature Completion & Deliverables Status

All 10 Core Domains from the Capstone Specification are fully implemented, validated, and live:

| # | Domain & Feature Area | Status | Implementation Details |
|---|---|:---:|---|
| **1** | **Admin & Flight Management** | ✅ **100% Done** | Create flights with physical seat layout (20 First, 30 Business, 50 Economy), seat capacity integrity validation, and schedule update cascade. |
| **2** | **Search & Fare Rules** | ✅ **100% Done** | Live available seat counts, class threshold validation, Basic Economy vs. Flexible Fares (+500 waitlist boost), multi-currency support. |
| **3** | **Concurrency & Overselling Prevention** | ✅ **100% Done** | Atomic PostgreSQL row-level locks (`SELECT ... FOR UPDATE`), 10-minute seat holds with auto-expiry, and `X-Idempotency-Key` headers. |
| **4** | **Booking Cutoffs & Fare Computation** | ✅ **100% Done** | Economy closed 60m before departure; First/Business closed 30m before departure. Dynamic fare calculation with flexible premiums. |
| **5** | **Cancellations & Travel Credits** | ✅ **100% Done** | Self-service & admin cancellation, partial group cancellation, automatic 1-year travel credit vouchers, and full refund tracking. |
| **6** | **Autonomous Waitlist (`SKIP LOCKED`)** | ✅ **100% Done** | Standby queue with priority formula (Loyalty Tier + Flexible fare + FIFO). n8n cron claims freed seats and sends 24h claim tokens. |
| **7** | **24-Hour Claim Redemption** | ✅ **100% Done** | Dedicated redemption portal (`/waitlist`) validating tokens and converting held seats to confirmed PNRs. |
| **8** | **Unified n8n Master Automation** | ✅ **100% Done** | Single pipeline with central **Switch Node** routing 7 independent branches (Check-in reminders, SLA escalation, Ops reports, Fraud bot). |
| **9** | **Security & Rate Limiting** | ✅ **100% Done** | In-memory sliding window rate limiter: Max 5 login attempts & 3 signups per 60s with `HTTP 429 Retry-After` headers. |
| **10** | **Policy AI Assistant (RAG)** | ✅ **100% Done** | Local ChromaDB vector store with Groq LLaMA-3.3 high-speed inference, rendering markdown into native high-contrast UI components. |

---

## 🚀 How to Run Locally (Step-by-Step)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/naumantariq5464-lgtm/flight-management-system.git
cd flight-management-system
```

---

### 2️⃣ Backend Setup (FastAPI + Neon PostgreSQL)
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
# Open .env and add your Neon Database URL and Groq API Key

# Start the Backend Server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **Swagger API Docs:** `http://127.0.0.1:8000/docs`
* **Health Endpoint:** `http://127.0.0.1:8000/health`

---

### 3️⃣ Frontend Setup (React 19 + Vite)
```bash
# Open a new terminal in the project root
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
* **Frontend Web App:** `http://localhost:5173`

---

### 4️⃣ n8n Cloud Master Workflow Setup
1. Log into your [n8n Cloud](https://smithackathon.app.n8n.cloud).
2. Go to **Workflows** ➔ **Add Workflow** ➔ Click `...` (Top Right) ➔ **"Import from File"**.
3. Select `n8n/flight_management_master_workflow.json`.
4. Connect your **Neon PostgreSQL** and **Gmail OAuth2** credentials.
5. Switch the toggle from **Inactive** to **ACTIVE (ON)**.

---

## 🔑 Default Credentials

### Single Super Admin Account
* **URL:** `http://localhost:5173/admin-login`
* **Email:** `admin@flightsystem.com`
* **Password:** `Admin@123456`
* **Role:** `SUPER_ADMIN`

### Customer Registration
* Customers can self-register at `http://localhost:5173/` (Protected by 3 requests/minute rate limiting).

---

## 🧪 Automated Testing & Verification

### 1. Test All n8n Automation Branches (1-Click)
Run the automated test suite from the `backend` directory:
```bash
cd backend
python test_n8n_master.py
```
This tests:
1. Waitlist Auto-Promotion
2. 24h Check-in Reminders
3. Refund SLA Escalations
4. Daily Ops KPI Reports
5. Live Flight Cancellation Alerts

### 2. Test Rate Limiting
Attempting more than 5 rapid logins triggers:
```json
HTTP/1.1 429 Too Many Requests
{
  "detail": "Rate limit exceeded: Maximum 5 requests per 60s. Please retry in 58 seconds."
}
```

---

## 📂 Project Structure

```
flight-management-system/
├── backend/
│   ├── app/
│   │   ├── auth/           # JWT & Super Admin Dependencies
│   │   ├── config/         # App Settings & Environment Loaders
│   │   ├── database/       # Async Engine & Session Factory
│   │   ├── models/         # SQLAlchemy 2.0 Async Models
│   │   ├── repositories/   # CRUD Database Access Layer
│   │   ├── routers/        # Admin, Customer, & Auth API Routes
│   │   ├── schemas/        # Pydantic v2 Request/Response Schemas
│   │   ├── services/       # Core Business Logic & Concurrency
│   │   └── utils/          # Enums, Exceptions, Rate Limiter, n8n Client
│   ├── requirements.txt    # Python Dependencies
│   ├── test_n8n_master.py  # Automation Test Runner
│   └── .env.example        # Backend Environment Template
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios API Client with Interceptors
│   │   ├── components/     # SeatMapModal, AuthModal, RAGChatWidget
│   │   ├── context/        # Auth & Toast Notification Providers
│   │   └── pages/          # Admin Dashboard, Search, Checkout, Waitlist
│   ├── package.json
│   └── vite.config.js
├── n8n/
│   └── flight_management_master_workflow.json # Unified Master Pipeline
├── rag/
│   ├── documents/          # Airline Policies (Markdown)
│   ├── chunking.py         # Semantic Section Chunking
│   ├── embedding.py        # HuggingFace MiniLM Embeddings
│   └── ingestion.py        # ChromaDB Vector Ingestion
├── .gitignore
├── .env.example
└── README.md
```

---


