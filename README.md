# ✈️ Production Flight Management & Autonomous Automation System

An enterprise-grade, high-concurrency **Flight Management System** built with **FastAPI**, **Neon Serverless PostgreSQL (Async Engine)**, **n8n Cloud Automation Engine**, **Local ChromaDB + Groq LLM Policy RAG**, and a **React 19 / Vite** high-contrast UI.

---

## 🏗️ System Architecture & Stack

```
                               ┌───────────────────────────┐
                               │   React 19 + Vite UI      │
                               │  (Customer + Operations)  │
                               └─────────────┬─────────────┘
                                             │ HTTP / REST
                                             ▼
                               ┌───────────────────────────┐
                               │     FastAPI Backend       │
                               │  (Async Row-Level Locks)  │
                               └──┬─────────────────────┬──┘
                                  │                     │
           Live Webhooks (POST)   │                     │ Direct AsyncPG Pooling
                                  ▼                     ▼
┌──────────────────────────────────────┐        ┌──────────────────────────┐
│          n8n Cloud Engine            │        │  Neon Serverless Postgres│
│ (Master Event Switch & Heartbeat)    │◄───────┤  (Single Ledger Truth)   │
└──────────────────┬───────────────────┘        └──────────────────────────┘
                   │ Direct SQL & Gmail
                   ▼
┌──────────────────────────────────────┐
│  - Waitlist Auto-Promotion           │
│  - Check-in Reminders (Suppression)  │
│  - Refund SLA Escalation Alert       │
│  - Daily Ops Revenue KPI Report      │
│  - Fraud & Bot Velocity Detection    │
│  - Expired Seat-Hold Reconciliation  │
│  - Live Flight Event Notifications   │
└──────────────────────────────────────┘
```

* **Backend Engine:** FastAPI (Python 3.14 / 3.11+), Pydantic v2, SQLAlchemy 2.0 Async, asyncpg.
* **Database Ledger:** Neon Serverless PostgreSQL with atomic `SELECT ... FOR UPDATE` & `SKIP LOCKED` concurrency guarantees.
* **Orchestration & Background Workflows:** n8n Cloud Master Workflow with unified Switch node routing.
* **Policy AI Assistant (RAG):** Local ChromaDB Vector Store (`all-MiniLM-L6-v2`) with Groq LLaMA-3.3 high-speed inference.
* **Frontend Application:** React 19, Vite, Lucide Icons, high-contrast monochrome design system.

---

## 📊 Comprehensive Feature Status & Implementation Matrix

| Domain | Feature Specification | Implementation Status | Core Mechanism |
|---|---|---|---|
| **Inventory & Schedule** | Dynamic Flight Creation (100 Seats: 20 First, 30 Business, 50 Economy) | ✅ **100% Completed** | Multi-class seat map auto-generator with physical seat positioning |
| **Inventory & Schedule** | Capacity Integrity & Integer Validation | ✅ **100% Completed** | Pydantic v2 validators preventing fractional or negative allocations |
| **Inventory & Schedule** | Flight Schedule Update & Cancellation Cascade | ✅ **100% Completed** | Audit logging + instant n8n webhook dispatch to affected travelers |
| **Concurrency & Booking** | Atomic Seat Decrement & Overselling Prevention | ✅ **100% Completed** | PostgreSQL Row-Level Locking (`SELECT ... FOR UPDATE`) |
| **Concurrency & Booking** | 10-Minute Temporary Seat Holds | ✅ **100% Completed** | Temporary hold tokens with countdown timer & automatic release |
| **Concurrency & Booking** | Idempotency Key Contract | ✅ **100% Completed** | `X-Idempotency-Key` caching header to prevent double charges |
| **Concurrency & Booking** | Class-Specific Booking Cutoffs | ✅ **100% Completed** | Economy 60m cutoff; First/Business 30m before departure |
| **Pricing & Policies** | Basic Economy vs. Flexible Fare Rules | ✅ **100% Completed** | Flexible fares allow free selection + +500 waitlist priority points |
| **Pricing & Policies** | Travel Credit Voucher Wallet | ✅ **100% Completed** | 1-year valid reusable voucher codes applied at checkout |
| **Waitlist & Standby** | Standby Queue with Priority Scoring | ✅ **100% Completed** | Formula: Loyalty tier points + Flexible fare boost + Join timestamp |
| **Waitlist & Standby** | Autonomous Waitlist Promotion (`SKIP LOCKED`) | ✅ **100% Completed** | n8n cron claims freed seats, holds them, & issues 24-hr claim token |
| **Waitlist & Standby** | 24-Hour Promotion Claim Redemption Portal | ✅ **100% Completed** | Dedicated UI input converting claim tokens to confirmed PNRs |
| **Automations & Ops** | 24-Hour Check-in Reminders | ✅ **100% Completed** | Hourly n8n scanner suppressing alerts if flight is cancelled |
| **Automations & Ops** | Refund SLA Escalation Alerts | ✅ **100% Completed** | Detects refunds pending >3 days and sends urgent alert to Admin |
| **Automations & Ops** | Executive Daily Operations Summary | ✅ **100% Completed** | Daily 23:59 summary: Revenue, confirmed bookings, load factors |
| **Automations & Ops** | Bot & Mass-Booking Velocity Detection | ✅ **100% Completed** | Flags >3 rapid bookings in 15m from identical IP/email |
| **Security & Auditing** | Sliding-Window Rate Limiting | ✅ **100% Completed** | Max 5 login attempts & 3 signups per 60s (HTTP 429 Retry-After) |
| **Security & Auditing** | Full Immutable Audit Trail | ✅ **100% Completed** | Complete record of admin/customer writes, diffs, and actor emails |
| **Policy AI Assistant** | Local ChromaDB Semantic Policy RAG | ✅ **100% Completed** | Embedded policies formatted into clean UI elements via Groq LLM |

---

## ⚡ Quickstart & Setup Guide

### 1. Prerequisites
* Python 3.11+ / 3.14
* Node.js 18+ and npm
* Neon PostgreSQL connection string
* Groq API Key (for RAG Assistant)
* n8n Cloud Account

---

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env with your Neon DB URL, Groq Key, and n8n webhook URL

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Health Check:** `http://127.0.0.1:8000/health`

---

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
* **Web App URL:** `http://localhost:5173`

---

### 4. n8n Cloud Automation Setup
1. Log into your [n8n Cloud instance](https://smithackathon.app.n8n.cloud).
2. Go to **Workflows** -> **Add Workflow** -> Click `...` (Top Right) -> **"Import from File"**.
3. Select the unified master workflow: `n8n/flight_management_master_workflow.json`.
4. Connect your **Neon PostgreSQL** and **Gmail OAuth2** credentials.
5. Switch the workflow toggle from **Inactive** to **ACTIVE (ON)**.

---

## 🧪 Testing the End-to-End Autonomous Lifecycle

### Step 1: Default Super Admin Credentials
* **Email:** `admin@flightsystem.com`
* **Password:** `Admin@123456`
* **Role:** `SUPER_ADMIN` (Full operational & inventory authority)

### Step 2: Customer Booking Flow
1. Visit `http://localhost:5173/` and search for flights (e.g., `LHE` → `DXB`).
2. Select seats on the interactive seat map (Economy, Business, or First Class).
3. Proceed to Checkout and complete booking with instantaneous PNR generation and printable electronic ticket receipt.

### Step 3: Automated Event Dispatch
Run the built-in n8n test suite to verify all switch branches:
```bash
cd backend
python test_n8n_master.py
```

### Step 4: Autonomous Waitlist Auto-Promotion
1. Navigate to **Waitlist Portal** (`/waitlist`) and join the standby queue for a flight.
2. Cancel an existing booking on that flight from **Manage Bookings** (`/manage-bookings`).
3. n8n's background job automatically claims the newly available seat with row-locking (`FOR UPDATE SKIP LOCKED`), promotes the passenger, generates a 24-hour claim token, and emails the passenger.
4. Enter the claim token into **Redeem Claim Token** to confirm the seat.

---

## 🛡️ License & Authorship
Developed as a production-grade Capstone Demonstration for Flight Management Systems, High-Concurrency Database Architecture, and Autonomous n8n Workflow Coordination.
