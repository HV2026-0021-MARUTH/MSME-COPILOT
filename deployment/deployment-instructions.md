# MARUTHI — Quick Start & Installation Guide

Welcome to **MARUTHI (AI Retail Copilot for Small Retailers)**!  
This guide will help you install, run, and test MARUTHI on your local machine in under **2 minutes**.

---

## 📋 System Prerequisites

Ensure you have the following installed on your system:
- **Git** (to clone the project)
- **Python 3.10+** (for the backend API & AI engines)
- **Node.js 18+ & npm** (for the web application UI)

---

## 🚀 1-Minute Setup & Launch

### 1️⃣ Step 1: Clone the Repository

Open your Terminal / Command Prompt and run:

```bash
git clone https://github.com/KSudheer21/msme-bi.git
cd msme-bi
```

---

### 2️⃣ Step 2: Start the Backend API (FastAPI)

Open **Terminal 1** and run:

#### 🪟 On Windows (PowerShell / CMD):
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 🍎 On macOS / Linux:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> **Note**: The backend automatically initializes a zero-setup SQLite database (`maruthi.db`) pre-seeded with realistic retail data on initial startup.

---

### 3️⃣ Step 3: Start the Frontend UI (React + Vite)

Open a **Second Terminal (Terminal 2)** and run:

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Accessing the Application

Once both servers are running:

| Component | Access URL | Description |
| :--- | :--- | :--- |
| **Web UI App** | **[http://localhost:3000](http://localhost:3000)** | Full Retail Copilot Dashboard & Views |
| **Backend API** | **[http://localhost:8000](http://localhost:8000)** | FastAPI REST Endpoints |
| **Interactive API Docs** | **[http://localhost:8000/docs](http://localhost:8000/docs)** | Swagger / OpenAPI Documentation |

---

## 💡 How to Demo Core Features

Once you open `http://localhost:3000`:

1. **📊 BI Dashboard (`Dashboard`)**:
   - View real-time revenue, gross profit, margin %, inventory valuation, and sales trend charts.
   - Click any product in **Top Sellers** to inspect single-product analytics cards.

2. **🗣️ Natural Sales Capture (`Record Sale / Invoice`)**:
   - Speak or type: `"Sold 3 Coca-Cola 250ml and 2 Lays Classic Salted 50g"`.
   - Watch instant deterministic server-side revenue (₹100) & profit (₹23) calculation.
   - Click **Confirm Sale** to reduce inventory.

3. **📄 Invoice AI Parser (`Record Sale / Invoice` -> `Invoice Upload`)**:
   - Upload any supplier invoice photo.
   - Review extracted items, costs, and selling prices with duplicate protection.
   - Click **Confirm Stock Update** to increase inventory.

4. **🤖 AI Business Advisor (`AI Advisor`)**:
   - View grounded daily action plans for tomorrow with explicit `FACT` vs `RECOMMENDATION` badges.
   - Ask custom business questions in natural language.

5. **📍 Seasonal & Local Intelligence (`Local Insights`)**:
   - Detect 3-tier location (GPS → Manual Locality → Default Store).
   - View climate drivers, upcoming Indian festivals, and grounded inventory recommendations.

6. **📑 Business Reports (`Reports`)**:
   - Export 100% numerically consistent business reports in **PDF**, **Excel (7 sheets)**, and **PNG Snapshot**.

---

## 🧪 Running Verification Tests

To verify tests on your system:

```bash
# Run 83 Backend Pytests (inside backend/ folder)
pytest

# Test Production Bundle Build (inside frontend/ folder)
npm run build
```

---

## ❓ Troubleshooting

- **Port 8000 in use**: Run `uvicorn app.main:app --port 8005` and update `frontend/vite.config.js` proxy target.
- **Node version mismatch**: Ensure Node.js is v18 or newer (`node -v`).
- **Python missing packages**: Ensure virtual environment is activated before running `pip install -r requirements.txt`.

---

## 🔮 Future Scope & Scalability Roadmap

> [!NOTE]
> *The features listed under **NEXT**, **SCALE**, and **VISION** represent future product roadmap capabilities and are not part of the current working hackathon MVP.*

### 1. TODAY — WORKING MVP (Implemented Capabilities)
- Natural sales capture, invoice OCR parsing, deterministic financial engine, real-time BI dashboard, demand forecasting, grounded AI advisor, local/seasonal intel, verifiable PDF/XLSX/PNG reports, 83/83 Pytests passing.

### 2. NEXT — PRODUCT SCALE (Future Roadmap)
- PostgreSQL/Supabase cloud DB deployment, multi-shop tenant isolation & RBAC auth, Indian regional language support (Hindi, Telugu, Tamil, etc.), offline-first PWA IndexedDB sync.

### 3. SCALE — RETAIL ECOSYSTEM (Future Roadmap)
- Automated wholesale purchase-order workflows, WhatsApp Business voice-bot integration, POS & payment gateway (UPI/Tally/Zoho) integrations.

### 4. VISION — "AI Operating System for Small Retailers"
- Positioning MARUTHI as an end-to-end AI OS where small Kirana retailers manage sales, stock, demand forecasting, and supplier ordering seamlessly via voice and mobile.

