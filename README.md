# MARUTHI — AI Retail Copilot for Small Retailers

**Problem Statement ID**: HV-MSME-05  
**Title**: MSME Business Intelligence Dashboard with Sales Analysis & Demand Forecasting  
**Domain**: Smart Manufacturing, MSMEs & Industry 6.0  

---

## Core Promise
A small retailer should be able to run basic business intelligence using only a phone, without expensive POS machines, barcode scanners, or specialized hardware.

---

## Architecture & Core Tech Stack

- **Frontend**: React + Vite (PWA-ready responsive layout, Lucide Icons, Recharts)
- **Backend**: FastAPI (Python), SQLAlchemy, Pydantic
- **Database**: PostgreSQL / Supabase compatible DDL schema (`database/schema.sql`) with zero-setup SQLite for local dev & testing.
- **Financial Rule Engine**: Pure deterministic calculations for Revenue, COGS, Gross Profit, Gross Margin %, and Inventory management.

---

## Project Structure

```
maruthi/
├── frontend/             # React + Vite web application
├── backend/              # FastAPI application and domain logic
│   ├── app/
│   │   ├── main.py       # App entry & GET /api/health
│   │   ├── config.py     # Configuration settings
│   │   ├── api/          # Dashboard, inventory, sales, purchases, advisor, reports, intelligence
│   │   ├── services/     # Analytics, forecasting, invoice/sales parsers, seasonal/local intelligence
│   │   ├── db/           # SQLAlchemy models & database sessions
│   │   └── schemas/      # Pydantic schemas
│   └── tests/            # Pytest suite
├── database/
│   ├── schema.sql        # PostgreSQL / Supabase DDL
│   └── seed.sql          # Realistic demo store seed data
├── reports/              # Report generation output directory
└── README.md
```

---

## Setup & Running

### 1. Backend Setup & Test Runner

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run Unit Tests
pytest

# Start Backend Server
uvicorn app.main:app --reload --port 8000
```

Verify backend health at: `http://localhost:8000/api/health`

### 2. Frontend Setup & Build

```bash
cd frontend
npm install

# Run Development Server
npm run dev

# Build Production Frontend Bundle
npm run build
```

---

## Core Financial & Inventory Rules

1. **Revenue**: `SUM(quantity × selling_price)`
2. **COGS**: `SUM(quantity × purchase_price)`
3. **Gross Profit**: `Revenue - COGS`
4. **Gross Margin %**: `(Gross Profit / Revenue) × 100`
5. **Inventory Purchases**: `inventory.quantity += purchased_quantity`
6. **Inventory Sales**: `inventory.quantity -= sold_quantity` (Negative inventory is strictly prohibited).

---

## Future Scope & Scalability Roadmap

> [!NOTE]
> *The features listed under **NEXT**, **SCALE**, and **VISION** represent future product roadmap capabilities and are not part of the current working hackathon MVP.*

### 1. TODAY — WORKING MVP (Implemented Capabilities)
- **Natural-Language Sales Capture**: Speech-to-text & NLP phrase parser (`EXACT`, `MATCHED`, `AMBIGUOUS`).
- **Human Review & Stock Safety**: Explicit transaction review before committing; strict anti-negative stock guard.
- **AI Wholesale Invoice Ingestion**: Vision & OCR invoice parser with duplicate invoice protection & new product modal validation.
- **Deterministic Financial Engine**: Pure server-side calculations for Revenue, COGS, Gross Profit, and Gross Margin %.
- **Real-Time BI Dashboard**: Metric cards, interactive Recharts sales trends, top sellers, and single-product analytics modal.
- **Deterministic Demand Forecasting**: Weighted moving average (`0.5*7d + 0.3*prev7d + 0.2*30d`), coverage days, stock risk, and reorder math.
- **Grounded AI Business Advisor**: Evidence-based action plan with `[FACT]` vs `[RECOMMENDATION]` badges and deterministic fallback engine.
- **Seasonal & Local Intelligence**: 3-tier location resolver (GPS → Manual → Store Default) + Indian festival demand drivers.
- **Multi-Format Business Reports**: 100% numerically consistent exports in PDF, 7-sheet Excel (XLSX), and PNG dashboard cards.
- **Responsive UI & Quality**: Mobile/Tablet/Laptop/PC responsive layout with 83/83 automated Pytests passing.

### 2. NEXT — PRODUCT SCALE (Future Roadmap)
- **Cloud Database Deployment**: Migration from zero-setup SQLite to PostgreSQL / Supabase cloud database (`schema.sql` ready).
- **Multi-Shop Architecture**: Tenant isolation, multi-store support, and role-based access control (RBAC).
- **Multilingual Local Support**: Indian regional language support (Hindi, Telugu, Tamil, Kannada, Marathi, etc.).
- **Offline-First PWA Sync**: Local IndexedDB caching with background server synchronization for poor-connectivity Kirana environments.
- **Advanced Model Routing**: Dynamic AI provider fallback and cost-optimized prompt routing.

### 3. SCALE — RETAIL ECOSYSTEM (Future Roadmap)
- **Supplier & Distributor Integration**: Direct B2B wholesale catalog sync and automated purchase-order generation.
- **WhatsApp & Voice Bot**: WhatsApp Business integration for Kirana store owners to query stock & record sales via voice notes.
- **Payment & Accounting Integration**: Connections with UPI/POS payment gateways and Tally/Zoho accounting platforms.

### 4. VISION — "AI Operating System for Small Retailers"
Positioning MARUTHI as an end-to-end AI OS where any Kirana retailer can naturally manage sales, inventory, demand forecasting, supplier reordering, and business intelligence using voice and mobile messaging.

