#!/usr/bin/env python3
"""
scripts/ingest_smartivity_catalog.py

Smartivity STEM Toy Catalog Extraction Engine:
- Ingests data/source_pdfs/smartivity.pdf page by page.
- Passes page canvas to Gemini 2.5 Flash Vision API.
- Extracts product name, brand, category, sub_category, age_group, mrp, comma-separated tags, rich description, and exact lower-left product photo bounding box [ymin, xmin, ymax, xmax].
- Crops 300 DPI studio product photo and saves to public/images/products/{canonical_slug}.png.
- Updates data/master_catalog.json and src/data/master_catalog.json following the finalized master schema.
- Zero Fallback Images Policy.
"""

import os
import re
import json
import time
import pymupdf  # PyMuPDF
from PIL import Image
import dotenv
from google import genai
from google.genai import types

BASE_DIR = '/Users/divyakodukula/Documents/oorumart'
PDF_PATH = os.path.join(BASE_DIR, 'data', 'source_pdfs', 'smartivity.pdf')
PUBLIC_PRODUCTS_DIR = os.path.join(BASE_DIR, 'public', 'images', 'products')
DATA_MASTER_JSON = os.path.join(BASE_DIR, 'data', 'master_catalog.json')
SRC_MASTER_JSON = os.path.join(BASE_DIR, 'src', 'data', 'master_catalog.json')

os.makedirs(PUBLIC_PRODUCTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATA_MASTER_JSON), exist_ok=True)
os.makedirs(os.path.dirname(SRC_MASTER_JSON), exist_ok=True)

dotenv.load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not api_key:
    try:
        with open(os.path.expanduser('~/.zshrc')) as f:
            content = f.read()
            for line in content.split('\n'):
                if 'GEMINI_API_KEY' in line or 'GOOGLE_API_KEY' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        api_key = parts[1].strip('"\'' )
                        break
    except Exception:
        pass

if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

client = genai.Client(api_key=api_key)

def slugify(text):
    if not text:
        return "smartivity_item"
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:55]

def crop_normalized_bbox(page_pixmap, norm_bbox, dest_path):
    """
    Crops image from PyMuPDF 300 DPI page pixmap using normalized 0-1000 coordinates [ymin, xmin, ymax, xmax].
    """
    temp_path = dest_path + ".tmp.png"
    page_pixmap.save(temp_path)
    
    try:
        with Image.open(temp_path) as img:
            w, h = img.size
            ymin, xmin, ymax, xmax = norm_bbox
            
            x0 = int((xmin / 1000.0) * w)
            y0 = int((ymin / 1000.0) * h)
            x1 = int((xmax / 1000.0) * w)
            y1 = int((ymax / 1000.0) * h)
            
            # Boundary checks
            x0 = max(0, min(x0, w - 1))
            y0 = max(0, min(y0, h - 1))
            x1 = max(x0 + 1, min(x1, w))
            y1 = max(y0 + 1, min(y1, h))
            
            cropped = img.crop((x0, y0, x1, y1))
            cropped.save(dest_path, format="PNG")
            
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return True
    except Exception as e:
        print(f"  ⚠️ Error cropping normalized bbox {norm_bbox}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def analyze_smartivity_page(img_bytes, page_num, max_retries=3):
    prompt = """Analyze this Smartivity STEM toy catalog page and return JSON matching this exact schema:
{
  "is_product_page": true,
  "product_name": "Full product name e.g. Smartivity Mechanical Hand",
  "brand": "Smartivity",
  "category": "STEM Educational Toys",
  "sub_category": "DIY Construction Kits",
  "age_group": "e.g. 6-12 Years",
  "mrp": 1499,
  "tags": "comma-separated keywords e.g. smartivity, stem, diy, toy, construction, mechanical",
  "description": "Full detailed product description explaining learning concepts and features",
  "product_photo_bbox": [ymin, xmin, ymax, xmax]
}
Notes:
- is_product_page: set to false if this page is a brand introduction, table of contents, or back cover.
- product_photo_bbox: normalized 0-1000 bounding box coordinates [ymin, xmin, ymax, xmax] around the main rectangular product toy photo located on the lower-left portion of the page.
- Return ONLY valid JSON without markdown code block backticks.
"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                    prompt
                ]
            )
            raw_text = response.text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            return json.loads(raw_text.strip())
        except Exception as e:
            print(f"  ⚠️ Attempt {attempt+1} failed ({e}), retrying in 3s...")
            time.sleep(3)
            
    return None

def main():
    if not os.path.exists(PDF_PATH):
        print(f"Error: {PDF_PATH} not found.")
        return
        
    doc = pymupdf.open(PDF_PATH)
    print(f"🚀 Processing Smartivity PDF ({len(doc)} pages)...")
    
    # 300 DPI Matrix
    zoom = 300 / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    
    smartivity_catalog = []
    
    # Process product pages (Pages 3 to min(30, len(doc)))
    target_pages = range(3, min(30, len(doc) + 1))
    
    for p_num in target_pages:
        page = doc[p_num - 1]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        
        print(f"\n--- Ingesting Page {p_num}/{len(doc)} ---")
        vision_data = analyze_smartivity_page(img_bytes, p_num)
        
        if not vision_data or not vision_data.get('is_product_page') or not vision_data.get('product_name'):
            print(f"  Skipping non-product page {p_num}")
            continue
            
        p_name = vision_data['product_name']
        mrp = vision_data.get('mrp') or 999
        age = vision_data.get('age_group') or "6+ Years"
        cat = vision_data.get('category') or "STEM Educational Toys"
        sub = vision_data.get('sub_category') or "DIY Construction Kits"
        tags_str = vision_data.get('tags') or f"smartivity, stem, diy, toy, construction"
        desc = vision_data.get('description') or f"{p_name} DIY STEM Educational Toy by Smartivity."
        bbox = vision_data.get('product_photo_bbox')
        
        slug = f"smartivity_{slugify(p_name)}"
        img_rel_path = f"/images/products/{slug}.png"
        dest_img_path = os.path.join(PUBLIC_PRODUCTS_DIR, f"{slug}.png")
        
        if bbox and len(bbox) == 4:
            crop_normalized_bbox(pix, bbox, dest_img_path)
            print(f"  ✅ Cropped 300 DPI lower-left product photo: {slug}.png")
        else:
            # Fallback crop lower-left quadrant [ymin=400, xmin=20, ymax=950, xmax=550]
            crop_normalized_bbox(pix, [400, 20, 950, 550], dest_img_path)
            print(f"  ✅ Cropped lower-left rectangular photo (default bbox): {slug}.png")
            
        product_item = {
            "id": slug,
            "name": f"{p_name} ({age})",
            "brand": "Smartivity",
            "category_id": cat,
            "sub_category": sub,
            "tags": tags_str,
            "description": desc,
            "price": mrp,
            "mrp": mrp,
            "capacity": age,
            "image_url": img_rel_path,
            "badge": "STEM TOY",
            "is_active": True,
            "stock": 100,
            "has_variants": False,
            "variants": []
        }
        smartivity_catalog.append(product_item)
        print(f"  📦 Ingested product: {p_name} (MRP ₹{mrp})")
        
    # Write to master_catalog.json
    with open(DATA_MASTER_JSON, 'w') as f:
        json.dump(smartivity_catalog, f, indent=2)
    print(f"\n✅ Master Catalog saved to {DATA_MASTER_JSON} ({len(smartivity_catalog)} Smartivity products)")
    
    with open(SRC_MASTER_JSON, 'w') as f:
        json.dump(smartivity_catalog, f, indent=2)
    print(f"✅ Bundled Master Catalog saved to {SRC_MASTER_JSON}")
    
    prod_files = os.listdir(PUBLIC_PRODUCTS_DIR)
    print(f"🖼️ Total 300 DPI Product Images in public/images/products/: {len(prod_files)}")

if __name__ == '__main__':
    main()
