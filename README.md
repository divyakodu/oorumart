# Oorumart & YesFancy — Multi-Tenant E-Commerce Platform

A high-performance multi-tenant hyper-local e-commerce platform built with **Astro**, **Tailwind CSS**, and **Supabase Cloud Database & Storage**.

---

## 📦 Supplier Catalog Ingestion & Cloud Synchronization Pipeline

This project includes automated, reusable Python CLI utilities to ingest supplier catalogs (PDF price lists, scanned image dumps, and Excel workbooks) into the master storefront schema and sync them with Supabase.

### Overview of Workflow

```
┌─────────────────────────────────┐
│ Supplier Catalogs (PDF / Images)│
└────────────────┬────────────────┘
                 │
                 ▼  scripts/extract_supplier_catalog.py
┌─────────────────────────────────┐
│ Draft Excel (.xlsx) & JSON file │
└────────────────┬────────────────┘
                 │  (Merchant edits prices/details)
                 ▼  scripts/sync_excel_to_cloud.py
┌─────────────────────────────────┐
│   Supabase Cloud DB & Storage   │ (Drafts set to is_active: false)
└────────────────┬────────────────┘
                 │
                 ▼  /admin?shop=yesfancy
┌─────────────────────────────────┐
│ Merchant uploads photo & toggles│ ──► Live on Storefront
└─────────────────────────────────┘
```

---

### 1. Extract Supplier Catalogs to Excel & JSON

Extracts model names, capacities, exact MRPs, and descriptions from supplier PDFs (Milton, GO24, Pexpo, Doms, Smartivity, Play Panda, Hasbro, Nerf, Bella Vita, etc.) and performs automatic cross-file deduplication.

```bash
# Run default extraction across all supplier catalogs
python3 scripts/extract_supplier_catalog.py

# Specify custom input directory or output file paths
python3 scripts/extract_supplier_catalog.py \
  --input-dir "/path/to/supplier_catalogs" \
  --output-excel "data/draft_catalog_import.xlsx" \
  --output-json "data/draft_catalog_import.json"

# Fast mode (vector text only, skip OCR for images)
python3 scripts/extract_supplier_catalog.py --no-ocr
```

* **Generated Excel**: `data/draft_catalog_import.xlsx` (Formatted with navy headers, cell borders, right-aligned prices, `MRP (₹)`, `Discount (%)`, and auto-adjusted widths).
* **Generated JSON**: `data/draft_catalog_import.json`.
* **Discount-First Pricing Model**: Selling price is derived directly from MRP and trade discount: $\text{Selling Price} = \text{round}(\text{MRP} \times (1 - \text{Discount} / 100))$. Default trade discount margins are applied automatically per brand:
  - **Pexpo**: `20%`
  - **Milton**: `15%`
  - **Ekta**: `15%`
  - **Smartivity**: `10%`
  - **DOMS**: `5%`
  - **Other / Unmapped**: `0%`
* **Storefront Safety**: All extracted entries default to `is_active: false` and `image_url: ""` so they remain completely invisible to customer browsing until activated.

---

### 2. Synchronize Excel / JSON to Supabase Cloud Database

Converts any edited Excel workbook into schema-compliant JSON and batch-upserts the products into Supabase Cloud Database under the selected merchant shop.

```bash
# Standard sync: Excel -> JSON -> Supabase Cloud DB (YesFancy shop by default)
python3 scripts/sync_excel_to_cloud.py --excel data/draft_catalog_import.xlsx

# Dry-run: Convert Excel to JSON only without updating Supabase
python3 scripts/sync_excel_to_cloud.py --excel data/draft_catalog_import.xlsx --dry-run

# Target a specific shop slug (e.g. yesfancy, varasiddhi, mumbai_paan)
python3 scripts/sync_excel_to_cloud.py --excel data/draft_catalog_import.xlsx --shop yesfancy
```

---

### 3. Merchant Publishing Workflow (Admin Portal)

Once synced to the database, the shopkeeper can review, photograph, and publish products live:

1. Open the Admin Portal: [`http://localhost:4321/admin?shop=yesfancy`](http://localhost:4321/admin?shop=yesfancy) *(or live on domain)*.
2. Navigate to the **Store Products** tab.
3. Filter by **⚪ Hidden Only** to view newly ingested draft entries.
4. Click **Edit** on any product to upload a product photo from a phone or computer (automatically uploaded to Supabase Storage isolated under `product-images/{shop_slug}/products/`).
5. Flip the status switch from **`⚪ Hidden`** to **`🟢 Active`** to instantly publish the product live on the storefront.

---

## 🛠️ Requirements & Dependencies

Make sure the following Python dependencies are installed:

```bash
pip install pymupdf openpyxl pytesseract pillow
```

*(Note: If using OCR fallback on scanned pages, ensure Tesseract is installed, e.g., `brew install tesseract` on macOS).*
