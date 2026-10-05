---
name: pdf-catalog-ingestion
description: "Automated end-to-end PDF & Screenshot catalog extraction pipeline: 300 DPI high-res rendering or screenshot-assisted alignment, lossless WebP asset compression (<60KB), finalized Master Catalog JSON generation, zero fallback images policy, and atomic local JSON + Supabase Cloud DB publishing."
---

# 📚 PDF Catalog Ingestion & E-Commerce Asset Extraction Skill

Use this skill whenever you need to ingest a new PDF supplier/brand catalog (e.g. `Bella Vita`, `Smartivity`, `GO24`, `Milton`, `Hasbro`, `Nerf`) into the Oorumart e-commerce storefront (`yesfancy` or other shops).

---

## 🎯 Core Principles & Architecture Rules

1. **Source Assets Directory Enforcement**:
   - All input supplier catalog PDFs MUST be stored in `data/source_pdfs/` or downloaded supplier paths (e.g. `~/Downloads/download_plugin/bell.pdf`).
   - Clean product screenshot dumps (when provided) are placed in `experiments/screenshots/`.

2. **Zero Fallback Images Policy & WebP Format**:
   - **NO placeholder or generic fallback images** (`offer_gift_store.jpg`, `mug.jpg`, `keychain.jpg`, `coasters.jpg`, etc.) are permitted.
   - Every product entry MUST map directly to an authentic product photo extracted from its source PDF or high-resolution studio screenshot.
   - **MANDATORY WebP Format**: All product images MUST be saved under `public/images/products/{brand}_{canonical_slug}.webp` using Pillow quality 85.
   - Files must stay under 60 KB each to guarantee sub-second page loads and zero Git repository bloat.

3. **Single Master Catalog JSON**:
   - All catalog products across all brands are merged into `src/data/master_catalog.json` and mirrored to `data/master_catalog.json`.

---

## 📄 Master Catalog JSON Schema Specification

Every product entry in `src/data/master_catalog.json` follows this finalized structure:

```json
[
  {
    "id": "bellavita_ocean_man_edp_100ml",
    "name": "Bella Vita Ocean Man Luxury Eau De Parfum (100ml)",
    "brand": "Bella Vita Luxury",
    "category_id": "fashion",
    "sub_category": "Eau De Parfum",
    "tags": "fashion, lifestyle, fragrance, perfume, luxury, gifts, bellavita, ocean man",
    "description": "Premium luxury fragrance for men. Top notes: Aldehydic, Aqueous, Fresh. Heart: Orchid, Ozonic, Floral. Base: Ambergris, Musk, Woody.",
    "price": 899,
    "mrp": 899,
    "capacity": "100ml",
    "image_url": "/images/products/bellavita_ocean_man_edp_100ml.webp",
    "badge": "LUXURY",
    "is_active": true,
    "stock": 50,
    "has_variants": false
  }
]
```

---

## 🛠️ Ingestion Workflows

### Method A: Direct PDF Extraction (Vector Text + 300 DPI Canvas)
Use when supplier PDF contains clean vector artwork and high-res embedded graphics:
1. Extract vector text blocks with PyMuPDF to map model names, prices, and volumes.
2. Render page bounding boxes at 300 DPI.
3. Trim printed price tags and save as `.webp`.

### Method B: Screenshot-Assisted Ingestion (When User Provides Product Crops)
Use when supplier PDF has complex vector layouts and pre-cropped studio photos are supplied (e.g. Bella Vita):
1. **Sort Screenshots Chronologically**: User captures follow page sequence order.
2. **Text Block Alignment**: Match each screenshot index 1:1 with catalog page price blocks.
3. **Lossless WebP Optimization**:
   ```python
   im = Image.open(src_path).convert("RGB")
   im.thumbnail((600, 600), Image.Resampling.LANCZOS)
   im.save(webp_path, "WEBP", quality=85, method=6)
   ```
4. **Master Catalog Merge**: Update `src/data/master_catalog.json` preserving existing products from other brands.
5. **Supabase Cloud DB Synchronization**:
   - Always authenticate using `SUPABASE_SERVICE_ROLE_KEY` to bypass Row-Level Security (RLS).
   - Use `on_conflict=shop_id,id` with `Prefer: resolution=merge-duplicates`.
   - Batch insert in chunks of 50.

---

## 🚀 Reusable Execution Commands

Run the standalone Bella Vita ingestion engine:
```bash
python3 scripts/ingest_bellavita_catalog.py
```
