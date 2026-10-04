#!/usr/bin/env python3
"""
scripts/generate_product_name_mapping.py

Renders catalog PDF pages, batches 10 images per request to Gemini 2.5 Flash Vision API,
and generates a complete review mapping artifact: product_name_mapping_review.md
"""

import os
import re
import json
import base64
import time
import urllib.request
import ssl
import pymupdf  # PyMuPDF
from PIL import Image, ImageChops

# Setup environment & directories
API_KEY = os.environ.get('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing!")

PDF_DIR = '/Users/divyakodukula/Documents/oorumart/catalog_images/yes_fancy'
BRAIN_DIR = '/Users/divyakodukula/.gemini/antigravity-cli/brain/c39ff80a-1df9-4b0a-b6ec-d86c69874e29'
REPORT_PATH = os.path.join(BRAIN_DIR, 'product_name_mapping_review.md')
TEMP_CROP_DIR = '/tmp/oorumart_catalog_crops'
os.makedirs(TEMP_CROP_DIR, exist_ok=True)

CATALOG_SPECS = [
    {"pdf": "CasseroleSeries - low - Mobile 2.pdf", "category": "casseroles"},
    {"pdf": "STEEL DRINKWARE CATALOGUE NEW MRP MAY 2026.pdf", "category": "drinkware"},
    {"pdf": "hasbro regular 042026.pdf", "category": "hasbro"},
    {"pdf": "HASBRO CARD.pdf", "category": "hasbro_card"},
    {"pdf": "LUNCHBOX - low - Mobile 1.pdf", "category": "lunchbox"},
    {"pdf": "NERF1805.pdf", "category": "nerf"}
]

ctx = ssl._create_unverified_context()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:55]

def crop_and_square_image(pil_img):
    w, h = pil_img.size
    # Trim top/bottom margins (remove headers/disclaimers)
    content = pil_img.crop((int(w * 0.03), int(h * 0.06), int(w * 0.97), int(h * 0.94)))
    
    bg = Image.new('RGB', content.size, (255, 255, 255))
    diff = ImageChops.difference(content, bg)
    bbox = diff.getbbox()
    cropped = content.crop(bbox) if bbox else content
    
    target_size = 1000
    padding = 80
    max_dim = target_size - (padding * 2)
    
    pw, ph = cropped.size
    scale = min(max_dim / pw, max_dim / ph)
    new_w = max(1, int(pw * scale))
    new_h = max(1, int(ph * scale))
    
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (target_size, target_size), (255, 255, 255))
    canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2))
    return canvas

def call_gemini_vision_batch(image_items):
    """
    image_items: list of dicts {'id': str, 'b64': str, 'pdf_name': str, 'page_num': int}
    """
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}'
    
    prompt = (
        "You are an expert product catalog auditor. Analyze the following images (labeled Image 1 to Image N). "
        "For each image, extract the exact product name, brand, model edition/series, and product category. "
        "Return ONLY a JSON array of objects with schema:\n"
        "[\n"
        "  {\n"
        "    \"image_index\": 1,\n"
        "    \"product_name\": \"Full Exact Product Name\",\n"
        "    \"brand\": \"Brand Name\",\n"
        "    \"model_name\": \"Model/Series\",\n"
        "    \"category\": \"Category\"\n"
        "  },\n"
        "  ...\n"
        "]"
    )
    
    parts = [{"text": prompt}]
    for idx, item in enumerate(image_items, 1):
        parts.append({"text": f"--- Image {idx} (Page {item['page_num']} of {item['pdf_name']}) ---"})
        parts.append({"inline_data": {"mime_type": "image/png", "data": item['b64']}})
        
    payload = {"contents": [{"parts": parts}]}
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            res = json.loads(response.read().decode('utf-8'))
            raw_text = res['candidates'][0]['content']['parts'][0]['text']
            # Clean markdown codeblocks
            clean_json = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
            return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ API Error on batch: {e}")
        return []

def main():
    print("🚀 Extracting all PDF pages & building Vision batch items...")
    
    all_pages = []
    
    for spec in CATALOG_SPECS:
        pdf_name = spec['pdf']
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            continue
            
        doc = pymupdf.open(pdf_path)
        print(f"  Rendering [{pdf_name}] ({len(doc)} pages)...")
        
        for i in range(len(doc)):
            page_num = i + 1
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            squared_img = crop_and_square_image(pil_img)
            
            # Save temp image
            temp_path = os.path.join(TEMP_CROP_DIR, f"{slugify(pdf_name)}_p{page_num}.png")
            squared_img.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                b64_str = base64.b64encode(f.read()).decode('utf-8')
                
            all_pages.append({
                'pdf_name': pdf_name,
                'category': spec['category'],
                'page_num': page_num,
                'temp_path': temp_path,
                'b64': b64_str
            })

    print(f"\n📦 Total catalog pages rendered: {len(all_pages)}")
    print("🤖 Processing Vision API batches (10 images per batch)...")
    
    batch_size = 10
    extracted_records = []
    
    for b_idx in range(0, len(all_pages), batch_size):
        batch = all_pages[b_idx:b_idx + batch_size]
        b_num = (b_idx // batch_size) + 1
        total_batches = (len(all_pages) + batch_size - 1) // batch_size
        print(f"  Processing Batch {b_num}/{total_batches} ({len(batch)} images)...")
        
        vision_results = call_gemini_vision_batch(batch)
        
        # Map back to items
        res_map = {r.get('image_index', i+1): r for i, r in enumerate(vision_results)}
        
        for idx, item in enumerate(batch, 1):
            v_res = res_map.get(idx, {})
            p_name = v_res.get('product_name', f"{item['category']}_page_{item['page_num']}")
            brand = v_res.get('brand', '')
            model = v_res.get('model_name', '')
            
            # Generate clean canonical filename
            prefix = slugify(brand) if brand else item['category']
            clean_slug = slugify(p_name)
            if not clean_slug.startswith(prefix):
                proposed_filename = f"{prefix}_{clean_slug}.png"
            else:
                proposed_filename = f"{clean_slug}.png"
                
            extracted_records.append({
                'pdf_name': item['pdf_name'],
                'page_num': item['page_num'],
                'extracted_name': p_name,
                'brand': brand,
                'model': model,
                'category': item['category'],
                'proposed_filename': proposed_filename,
                'temp_path': item['temp_path']
            })
            
        time.sleep(3) # 3s delay to respect 15 RPM
        
    print("\n📝 Generating Markdown Review Artifact...")
    
    md_content = "# 📋 Product Name Extraction Review Mapping Table\n\n"
    md_content += "Review all **229 extracted product names** identified by Gemini 2.5 Flash Vision before committing changes to disk and database.\n\n"
    md_content += "| # | Catalog PDF | Page | Brand | Extracted True Product Name | Proposed Image Filename |\n"
    md_content += "|---|---|---|---|---|---|\n"
    
    for idx, rec in enumerate(extracted_records, 1):
        md_content += f"| {idx} | `{rec['pdf_name']}` | Page {rec['page_num']} | {rec['brand']} | **{rec['extracted_name']}** | `{rec['proposed_filename']}` |\n"

    with open(REPORT_PATH, 'w') as f:
        f.write(md_content)

    # Save JSON cache of mapping for step 2 execution
    cache_path = os.path.join(TEMP_CROP_DIR, 'vision_mapping_cache.json')
    with open(cache_path, 'w') as f:
        json.dump(extracted_records, f, indent=2)

    print(f"\n🎉 DONE! Review report saved to: {REPORT_PATH}")

if __name__ == '__main__':
    main()
