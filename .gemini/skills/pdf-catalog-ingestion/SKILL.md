---
name: pdf-catalog-ingestion
description: "Automated end-to-end PDF catalog processing pipeline: 300 DPI high-res rendering, Gemini 2.5 Flash Vision API bounding-box crop + metadata parsing, user-friendly SEO image naming, and atomic local JSON + Supabase Cloud DB publishing."
---

# 📚 PDF Catalog Ingestion & E-Commerce Asset Extraction Skill

Use this skill whenever you need to ingest a new PDF supplier/brand catalog (e.g. Milton, Hasbro, Nerf, Casseroles, Drinkware) into the Oorumart e-commerce storefront (`yesfancy` or other shops).

---

## 🎯 Skill Capabilities & Workflow

1. **300 DPI 4K Print-Resolution Local Canvas Rendering**:
   - Renders PDF catalog pages at 300 DPI high-resolution canvas (`2304 x 3249+` pixels) so product images are 4K crisp with zero pixelation or jagged edges.

2. **100% Local CPU Vector Text & Exact Price Extraction**:
   - Reads exact catalog prices/MRPs directly from PDF vector text layers without needing external API calls or hitting rate limits.

3. **Automatic Price Tag Trimming (`crop_printed_tags`)**:
   - Inspects price block coordinates and trims off top/bottom header banners so printed price tags (`MRP 2299`, `MRP 449`) are 100% cropped out of image files.

4. **User-Friendly SEO Filename Generation**:
   - Names every extracted image file using clean, readable SEO slugs (e.g. `milton_thermosteel_duo_dlx_flask_1000ml.png`, `nerf_elite_2_0_commander_rd_6_blaster.png`).

5. **User Novelties Ingestion Engine**:
   - Ingests user-uploaded product photos from `catalog_images/yes_fancy/images/` and populates the `novelties` category.

6. **Atomic Local + Supabase DB Publishing**:
   - Simultaneously updates local JSON configuration (`src/shops/[shop].json`) AND Supabase Cloud Database tables (`categories` and `products`).

---

## 🛠️ Reusable Commands & Production Engine Scripts

### 1-Command Production Triggers:

#### 1. Full 300 DPI Catalog Ingestion (100% Local CPU, 0 API Calls):
```bash
.venv/bin/python scripts/build_exact_local_catalog.py
```

#### 2. Ingest User Novelty Images:
```bash
.venv/bin/python scripts/ingest_28_user_images.py
```

---

## 🔒 Security & Guidelines
- Always source `~/.zshrc` silently in background commands without logging or displaying `GEMINI_API_KEY` contents.
- Store catalog images in `/public/images/catalog_extracted/high_res_300dpi_full_catalog/`.
- Store user photos in `/public/images/catalog_extracted/user_uploaded_images/`.
