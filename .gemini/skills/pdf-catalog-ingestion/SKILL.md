---
name: pdf-catalog-ingestion
description: "Automated end-to-end PDF catalog extraction pipeline: 300 DPI high-res rendering, local PyMuPDF bounding-box studio crops, finalized Master Catalog JSON generation (with tags & descriptions), zero fallback images policy, and atomic local JSON + Supabase Cloud DB publishing."
---

# 📚 PDF Catalog Ingestion & E-Commerce Asset Extraction Skill

Use this skill whenever you need to ingest a new PDF supplier/brand catalog (e.g. `GO24`, `Milton`, `Hasbro`, `Nerf`, `Casseroles`, `Drinkware`) into the Oorumart e-commerce storefront (`yesfancy` or other shops).

---

## 🎯 Core Principles & Architecture Rules

1. **Source PDF Directory Enforcement**:
   - All input supplier catalog PDFs MUST be stored in `data/source_pdfs/`.
   - Examples:
     - `data/source_pdfs/GO24_Vaccum_Range_catalogue.pdf`
     - `data/source_pdfs/NERF1805.pdf`
     - `data/source_pdfs/STEEL DRINKWARE CATALOGUE NEW MRP MAY 2026.pdf`
     - `data/source_pdfs/CasseroleSeries - low - Mobile 2.pdf`
     - `data/source_pdfs/hasbro regular 042026.pdf`
     - `data/source_pdfs/HASBRO CARD.pdf`

2. **Zero Fallback Images Policy (Strict)**:
   - **NO placeholder or generic fallback images** (`offer_gift_store.jpg`, `mug.jpg`, `keychain.jpg`, `coasters.jpg`, etc.) are permitted.
   - Every product entry MUST map directly to an authentic 300 DPI studio product photo extracted from its source PDF or verified product photo.
   - Images are saved under `public/images/products/` with clean canonical slugs:
     - `public/images/products/go24_insulated_infinity_art_750ml.png`
     - `public/images/products/nerf_elite_2_0_slyshot.png`

3. **Single Master Catalog JSON**:
   - All catalog products across all brands are merged into `data/master_catalog.json` and mirrored to `src/data/master_catalog.json`.

---

## 📄 Master Catalog JSON Schema Specification

Every product entry in `data/master_catalog.json` MUST follow this finalized structure:

```json
[
  {
    "id": "go24_insulated_infinity_art_750ml",
    "name": "GO24 Infinity Art 3-Layer Insulated Bottle (750ml)",
    "brand": "GO24",
    "category_id": "Insulated Bottles",
    "sub_category": "Lifestyle - ART",
    "tags": "insulated, bottles, hot-cold, steel, lifestyle, art, 750ml",
    "description": "Premium 3-layer vacuum insulated stainless steel bottle featuring vibrant scratch-free art graphics. Keeps drinks ice-cold or piping hot for up to 24 hours. ISI certified food-grade steel.",
    "price": 1295,
    "mrp": 1295,
    "capacity": "750ml",
    "image_url": "/images/products/go24_insulated_infinity_art_750ml.png",
    "badge": "BESTSELLER",
    "is_active": true,
    "stock": 100,
    "has_variants": true,
    "variants": [
      {
        "variant_id": "go24_insulated_infinity_art_750ml",
        "capacity": "750ml",
        "mrp": 1295,
        "price": 1295,
        "image_url": "/images/products/go24_insulated_infinity_art_750ml.png"
      },
      {
        "variant_id": "go24_insulated_infinity_art_1000ml",
        "capacity": "1000ml",
        "mrp": 1425,
        "price": 1425,
        "image_url": "/images/products/go24_insulated_infinity_art_1000ml.png"
      }
    ]
  }
]
```

---

## 🛠️ Extraction & Ingestion Execution Steps

1. **Inspect PDF & Text Blocks**:
   - Run PyMuPDF text block extraction to map page numbers, model names, capacity variants (350ml, 750ml, 1000ml), and MRP prices.

2. **300 DPI Studio Photo Extraction**:
   - Render page bounding boxes at 300 DPI to generate crisp product photos without price tag overlays.
   - Save to `public/images/products/{canonical_slug}.png`.

3. **Generate Master JSON & Sync Database**:
   - Save output to `data/master_catalog.json` and `src/data/master_catalog.json`.
   - Update Supabase Cloud DB `products` table for shop `yesfancy`.
