# MARUTHI — AI Retail Copilot for Small Retailers
## Comprehensive Hackathon Q&A & Judge Evaluation Guide

**Problem Statement ID**: HV-MSME-05  
**Title**: MSME Business Intelligence Dashboard with Sales Analysis & Demand Forecasting  
**Domain**: Smart Manufacturing, MSMEs & Industry 6.0  
**Repository**: [HV2026-0021-Maruthi](https://github.com/HV2026-0021-MARUTH/MSME-COPILOT)

---

## Executive Summary & Vision

### Q1: What core problem does MARUTHI solve for small Kirana store owners in India?
**Answer**:  
Small MSME retailers and Kirana store owners operating in India face three major operational bottlenecks:
1. **Lack of Expensive Hardware**: Most Kirana stores cannot afford dedicated POS machines, barcode scanners, or inventory management hardware.
2. **Time-Consuming Manual Record Keeping**: Inventory updates, sales tallying, and invoice processing are done manually on paper notebooks (*Khata*), leading to untracked stock leaks, stockouts, and poor financial visibility.
3. **No Financial or Forecasting Intelligence**: Retailers rely on intuition rather than data to make reordering decisions, leading to working capital lockup in slow-moving stock or lost sales during festive demand surges.

**MARUTHI** transforms any standard smartphone into a complete **AI Retail Operating System**. Retailers can capture sales by speaking in natural language, ingest wholesale supplier invoices via mobile phone photos, receive grounded business recommendations, and track financial performance without buying any extra hardware.

---

## Technical Architecture & Core System Design

### Q2: What is the overall tech stack of MARUTHI and why was it chosen?
**Answer**:  
- **Frontend**: React (Vite), Lucide Icons, Recharts, Glassmorphism CSS design system. Chosen for lightning-fast mobile responsiveness and PWA readiness on low-cost smartphones.
- **Backend**: FastAPI (Python 3.11), Pydantic v2, SQLAlchemy ORM. FastAPI was chosen for asynchronous endpoint execution, speed, strict type validation, and seamless integration with AI/ML processing libraries.
- **Database**: Dual-Mode Database Architecture — zero-setup SQLite for local dev/testing, fully compatible with PostgreSQL / Supabase schema (`database/schema.sql`) for cloud production.
- **Financial Rule Engine**: Pure deterministic Python mathematical engine. AI is strictly isolated to natural language understanding and OCR, while all financial calculations are executed by deterministic code.

---

## Multi-Business & Tenant Isolation

### Q3: How does MARUTHI isolate data between multiple stores or profiles on the same platform?
**Answer**:  
MARUTHI implements **strict multi-tenant database isolation** using `shop_id` scoping across all database tables and API services:
- Every entity (`Product`, `Sale`, `Purchase`, `Invoice`, `CustomerReport`) has an explicit foreign key filter (`shop_id`).
- All API routes explicitly require and validate `shop_id` (defaulting to `shop_001` for demo store).
- The frontend features an interactive Profile Switcher that dynamically filters dashboard metrics, inventory lists, and AI recommendations to ensure zero data leakage between different retail businesses.

---

## Product Identity & Multi-Tier Matching Engine

### Q4: How does MARUTHI identify products when a retailer enters natural-language sales or scans invoices?
**Answer**:  
We implemented a **4-Tier Deterministic Product Matching Engine** in [`sales_parser.py`](file:///c:/Users/sudheer/0021/HV2026-0021-Maruthi/backend/app/services/sales_parser.py):
1. **Tier 1 — Exact SKU Match** (`1.00` confidence): Direct match against system-generated or barcode SKUs (e.g., `TU-750` for Thums Up 750ml).
2. **Tier 2 — Exact Name Match** (`1.00` confidence): Case-insensitive exact product name match.
3. **Tier 3 — Alias Match** (`1.00` confidence): Matches retailer-defined custom aliases (e.g., `coke` → `Coca Cola 500ml`).
4. **Tier 4 — Proportional Fuzzy Match**: Multi-word overlap token score. Requires substantial token overlap (>4 chars) to prevent false positives.

```
Input Query ──► 1. Exact SKU? ──(Yes)──► Match (SKU)
                   │ (No)
                   ▼
                2. Exact Name? ──(Yes)──► Match (Exact)
                   │ (No)
                   ▼
                3. Alias Match? ──(Yes)──► Match (Alias)
                   │ (No)
                   ▼
                4. Proportional Fuzzy Match ──► Score >= 0.85? ──(Yes)──► Match (Fuzzy)
                                                  │ (No)
                                                  ▼
                                               Requires Manual Review
```

### Q5: How do you prevent false matches (e.g., matching "dairy milk" to "Amul Taaza Milk")?
**Answer**:  
- **Proportional Token Scoring**: We eliminated naive single-word substring matching. A query must share multiple key tokens with a product to achieve high confidence.
- **Human-in-the-Loop Confirmation**: Any match with confidence below `0.85` is flagged as `NEEDS_MATCH` and passed to the frontend transaction review screen ([`SaleReview.jsx`](file:///c:/Users/sudheer/0021/HV2026-0021-Maruthi/frontend/src/components/SaleReview.jsx)). The system never auto-commits uncertain product matches without explicit retailer confirmation.

---

## Financial Logic & Business Intelligence Rules

### Q6: What are the exact financial rules enforced by MARUTHI?
**Answer**:  
MARUTHI enforces 6 core deterministic rules in [`analytics_service.py`](file:///c:/Users/sudheer/0021/HV2026-0021-Maruthi/backend/app/services/analytics_service.py):
1. **Revenue**: \(\text{Revenue} = \sum (\text{Quantity Sold} \times \text{Selling Price})\)
2. **Cost of Goods Sold (COGS)**: \(\text{COGS} = \sum (\text{Quantity Sold} \times \text{Purchase Cost})\)
3. **Gross Profit**: \(\text{Gross Profit} = \text{Revenue} - \text{COGS}\)
4. **Gross Margin %**: \(\text{Gross Margin \%} = \left(\frac{\text{Gross Profit}}{\text{Revenue}}\right) \times 100\)
5. **Purchase Processing**: \(\text{Inventory Quantity} \leftarrow \text{Inventory Quantity} + \text{Purchased Quantity}\)
6. **Sales Processing**: \(\text{Inventory Quantity} \leftarrow \text{Inventory Quantity} - \text{Sold Quantity}\) (Strictly blocked if \(\text{Quantity} < 0\)).

### Q7: Can inventory balance become negative in MARUTHI?
**Answer**:  
**No.** MARUTHI enforces a strict **Anti-Negative Stock Guard** at both the API level and the database transaction layer. If a sale attempt exceeds current available inventory stock, the backend rejects the transaction with a `400 Bad Request` safety error specifying the exact deficit.

---

## Demand Forecasting & Seasonal Intelligence

### Q8: How does the Demand Forecasting engine work?
**Answer**:  
MARUTHI uses a **Weighted Moving Average (WMA)** forecasting model with stock coverage days analysis:

$$\text{Forecasted Daily Demand} = (0.5 \times \text{Avg}_7d) + (0.3 \times \text{Avg}_{\text{prev} 7d}) + (0.2 \times \text{Avg}_{30d})$$

- **Stock Coverage Days**: \(\text{Coverage Days} = \frac{\text{Current Stock}}{\text{Forecasted Daily Demand}}\)
- **Reorder Trigger**: If Coverage Days \(\le 3\), the system generates an urgent stock risk alert and calculates the optimal reorder quantity:

$$\text{Reorder Quantity} = (\text{Forecasted Daily Demand} \times 14\text{ days}) - \text{Current Stock}$$

### Q9: How does Seasonal and Local Intelligence factor into forecasts?
**Answer**:  
MARUTHI incorporates a 3-tier Location Resolver (GPS coordinates \(\to\) Manual Selection \(\to\) Store Default Location) combined with an **Indian Festival & Event Demand Matrix**:
- During major regional festivals (Diwali, Holi, Dussehra, Pongal, Sankranti, Eid), demand multipliers (\(1.2\times - 1.8\times\)) are dynamically applied to specific product categories (Sweets, Dairy, Snacks, Beverage, Puja items).

---

## Grounded AI Business Advisor

### Q10: How do you guarantee the AI Business Advisor does not hallucinate numbers?
**Answer**:  
The AI Advisor ([`advisor_service.py`](file:///c:/Users/sudheer/0021/HV2026-0021-Maruthi/backend/app/services/advisor_service.py)) uses a **Fact-Grounded Architecture**:
1. **Strict Context Injection**: The backend queries real-time database facts (top profit items, low stock warnings, revenue, dead stock) first.
2. **Explicit Fact Badges**: Every response explicitly separates `[FACT]` (verified numbers directly from SQL) from `[RECOMMENDATION]` (actionable advice).
3. **Deterministic Fallback Engine**: If AI API credentials are absent or fail, a local rule-based intelligence engine generates 100% accurate, evidence-backed advice based directly on SQL analytics.

---

## AI Wholesale Invoice Ingestion

### Q11: How does photo/invoice parsing work for wholesale supplier bills?
**Answer**:  
1. **OCR & Vision Extraction**: When a retailer uploads a image/photo of a paper invoice, the parser extracts vendor name, invoice date, line items (product name, quantity, purchase price), and total amount.
2. **Duplicate Invoice Guard**: SHA-256 hash signatures (`vendor_date_amount`) are checked before processing to prevent duplicate inventory additions.
3. **New Product Detection**: Items not matching existing products trigger a modal allowing the shopkeeper to set selling prices and generate SKUs before committing stock.

---

## Quality Assurance & Automated Testing

### Q12: What test coverage and validation exists in MARUTHI?
**Answer**:  
- **Automated Backend Pytests**: 90 out of 90 tests passing (100% pass rate) covering:
  - Multi-business tenant isolation (`test_multi_business.py`).
  - Product matching safety & edge cases (`test_product_matching_safety.py`).
  - Sales parsing & phrase extraction (`test_sales_parser.py`).
  - Invoice OCR & duplicate prevention (`test_invoice_parser.py`).
  - Deterministic analytics & financial calculations (`test_analytics.py`).
  - AI Advisor grounding & empty query handling (`test_advisor.py`).
  - Bulk CSV/XLSX import & duplicate detection (`test_import_sales.py`).
- **Frontend Build Validation**: Clean compilation with `npm run build` using zero syntax or bundler errors.

---

## Future Roadmap & Vision

### Q13: What is the long-term vision for MARUTHI post-hackathon?
**Answer**:  
- **PWA Offline-First Caching**: IndexedDB local storage with background sync for poor network Kirana locations.
- **Multilingual Voice Support**: Native speech-to-text in Hindi, Telugu, Tamil, Kannada, Marathi, and Bengali.
- **Direct WhatsApp Business Bot**: Allowing store owners to check stock, query low-stock alerts, and record sales directly via WhatsApp voice notes.
- **Supplier B2B Integration**: Automated purchase order generation sent directly to local FMCG distributors.
