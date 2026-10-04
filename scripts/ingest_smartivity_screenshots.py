#!/usr/bin/env python3
"""
scripts/ingest_smartivity_screenshots.py

Ingests Smartivity product screenshots from experiments/screenshots/ using Gemini 3.5 Flash / Lite Vision.
- Identifies product name, age group, MRP, category, sub-category, tags, and rich description.
- Saves renamed, clean product images to public/images/products/smartivity_<slug>.png.
- Updates data/master_catalog.json and src/data/master_catalog.json matching Master Catalog JSON schema.
- Zero Fallback Images Policy.
"""

import os
import re
import glob
import json
import time
from PIL import Image
import dotenv
from google import genai
from google.genai import types

BASE_DIR = '/Users/divyakodukula/Documents/oorumart'
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'experiments', 'screenshots')
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
    print("❌ Error: GEMINI_API_KEY not found.")
    exit(1)

client = genai.Client(api_key=api_key)

def slugify(text):
    if not text:
        return "item"
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:55]

def analyze_screenshot(img_path):
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
        
    prompt = """Analyze this Smartivity STEM educational toy product image screenshot carefully and extract detailed metadata.
Return JSON matching this exact schema:
{
  "is_product_image": true,
  "product_name": "Full product title without 'Smartivity' prefix if redundant, e.g. '3D Maze', 'Mechanical Hand', 'Hydraulic Crane', 'Globe Trotter', 'Pinball Machine'",
  "brand": "Smartivity",
  "category": "STEM Educational Toys",
  "sub_category": "e.g. DIY Construction Kits, Mechanical Toys, Robotics & Hydraulics, Arcade & Skill Games, Science & Optics, Art & Music Kits",
  "age_group": "Age group visible or appropriate e.g. '6-12 Years', '8+ Years', '6+ Years'",
  "mrp": 1299,
  "badge": "e.g. STEM Toy, Top Seller, Educational",
  "tags": "comma-separated list of lower-case keywords (e.g. smartivity, stem, diy, toy, construction, mechanics, physics, learning)",
  "description": "Rich 2-3 sentence product summary explaining the core STEM learning concepts (hydraulics, momentum, gears, levers, optical physics, etc.), hands-on construction activity, skills developed, and key features."
}

Rules:
1. is_product_image: Set to false ONLY if this image is not a product screenshot (e.g. pure blank/unrelated page).
2. mrp: Look for price text in image. If missing, estimate realistic Smartivity catalog retail MRP in INR (integer, e.g. 799, 999, 1299, 1499, 1799, 1999).
3. tags: Must be a single comma-separated string, NOT an array.
4. Return ONLY valid JSON block without markdown formatting or code blocks if possible, or plain JSON.
"""

    models_to_try = [
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
        'gemini-3.8-flash',
        'gemini-flash-lite-latest',
        'gemini-flash-latest'
    ]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                    prompt
                ]
            )
            raw_text = response.text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:]
            elif raw_text.startswith('```'):
                raw_text = raw_text[3:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            return json.loads(raw_text.strip())
        except Exception as e:
            err_msg = str(e)
            if '429' in err_msg or 'RESOURCE_EXHAUSTED' in err_msg or '404' in err_msg:
                # Try next model
                continue
            else:
                time.sleep(1)
                
    return None

def process_all_screenshots():
    screenshots = sorted(glob.glob(os.path.join(SCREENSHOTS_DIR, '*.png')))
    print(f"🚀 Found {len(screenshots)} screenshots in {SCREENSHOTS_DIR}")
    
    catalog_items = []
    seen_slugs = {}
    
    for idx, img_path in enumerate(screenshots, start=1):
        filename = os.path.basename(img_path)
        print(f"\n[{idx}/{len(screenshots)}] Ingesting {filename}...")
        
        data = analyze_screenshot(img_path)
        if not data or not data.get('is_product_image') or not data.get('product_name'):
            print(f"  ⚠️ Could not parse product from {filename}, skipping.")
            continue
            
        raw_name = data['product_name'].strip()
        # Clean product name
        if raw_name.lower().startswith('smartivity '):
            clean_name = raw_name[11:].strip()
        else:
            clean_name = raw_name
            
        base_slug = f"smartivity_{slugify(clean_name)}"
        
        # Handle duplicate product names across screenshots
        if base_slug in seen_slugs:
            seen_slugs[base_slug] += 1
            final_slug = f"{base_slug}_{seen_slugs[base_slug]}"
            display_name = f"Smartivity {clean_name} (Variant {seen_slugs[base_slug]})"
        else:
            seen_slugs[base_slug] = 1
            final_slug = base_slug
            display_name = f"Smartivity {clean_name}"
            
        mrp = int(data.get('mrp') or 999)
        price = mrp
        age = data.get('age_group') or "6+ Years"
        cat = data.get('category') or "STEM Educational Toys"
        sub = data.get('sub_category') or "DIY Construction Kits"
        badge = data.get('badge') or "STEM Toy"
        
        tags_val = data.get('tags')
        if isinstance(tags_val, list):
            tags_str = ", ".join([str(t) for t in tags_val])
        else:
            tags_str = str(tags_val or f"smartivity, stem, diy, toy, construction, {slugify(clean_name).replace('_', ', ')}")
            
        desc = data.get('description') or f"Build and learn with {display_name}. High-quality DIY STEM construction kit."
        
        dest_filename = f"{final_slug}.png"
        dest_img_path = os.path.join(PUBLIC_PRODUCTS_DIR, dest_filename)
        rel_img_url = f"/images/products/{dest_filename}"
        
        # Copy / process image using PIL to ensure valid, high quality PNG
        try:
            with Image.open(img_path) as im:
                im.convert("RGB").save(dest_img_path, format="PNG")
            print(f"  ✅ Renamed & Saved: public/images/products/{dest_filename}")
        except Exception as e:
            print(f"  ❌ Error saving image {dest_img_path}: {e}")
            continue
            
        item = {
            "id": final_slug,
            "name": f"{display_name} ({age})",
            "brand": "Smartivity",
            "category_id": cat,
            "sub_category": sub,
            "tags": tags_str,
            "description": desc,
            "price": price,
            "mrp": mrp,
            "capacity": age,
            "image_url": rel_img_url,
            "badge": badge,
            "is_active": True,
            "stock": 50,
            "has_variants": False,
            "variants": []
        }
        
        catalog_items.append(item)
        print(f"  📦 Added product: {item['name']} | Price: ₹{mrp}")
        
        # Short pause between calls
        time.sleep(0.3)

    print(f"\n🎉 Successfully ingested {len(catalog_items)} Smartivity products!")
    
    # Save to JSON files
    with open(DATA_MASTER_JSON, 'w') as f:
        json.dump(catalog_items, f, indent=2)
    print(f"💾 Updated: {DATA_MASTER_JSON}")
    
    with open(SRC_MASTER_JSON, 'w') as f:
        json.dump(catalog_items, f, indent=2)
    print(f"💾 Updated: {SRC_MASTER_JSON}")

if __name__ == '__main__':
    process_all_screenshots()
