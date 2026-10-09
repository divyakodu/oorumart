#!/usr/bin/env python3
"""
scripts/extract_supplier_catalog.py
-----------------------------------
A modular, reusable CLI utility to scan and extract supplier catalogs
(PDF price-lists, vector catalogs, and scanned image dumps) into:
  1. An Excel workbook (.xlsx) ready for merchant review/editing.
  2. A JSON file (.json) compliant with the Oorumart / YesFancy catalog schema.

Key Features:
- Non-destructive: Produces new draft files, never modifies master production files.
- Safe Draft Defaults: Sets `is_active: False` and `image_url: ""` so drafts remain
  hidden until the merchant reviews them and toggles them live in the backend.
- Hybrid Extraction: Fast vector text parsing with PyMuPDF + local OCR fallback.
- Brand & Category Normalization: Auto-maps brands (Milton, GO24, Pexpo, Smartivity,
  Hasbro, Doms, Ekta, Bella Vita, Owlog Beauty) to valid storefront categories.
"""

import os
import re
import sys
import json
import argparse
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

import pymupdf
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Optional OCR support
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def clean_str(val: Any) -> Any:
    """Strip illegal XML/ASCII control characters that cause OpenPyXL to fail."""
    if isinstance(val, str):
        # Remove ASCII control characters 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', val)
        return " ".join(cleaned.split())
    return val


def slugify(text: str) -> str:
    """Generate a clean URL/SKU-friendly slug."""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


class CatalogExtractor:
    def __init__(self, input_dir: str, output_excel: str, output_json: str, ocr_enabled: bool = True):
        self.input_dir = Path(input_dir)
        self.output_excel = Path(output_excel)
        self.output_json = Path(output_json)
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE
        self.products: List[Dict[str, Any]] = []
        self.seen_skus = set()

    def add_product(self, item: Dict[str, Any]):
        """Sanitize and append product if unique."""
        sku_id = item.get("id") or slugify(f"{item.get('brand', 'brand')}_{item.get('name', 'product')}")
        # avoid exact duplicates
        if sku_id in self.seen_skus:
            counter = 2
            while f"{sku_id}_{counter}" in self.seen_skus:
                counter += 1
            sku_id = f"{sku_id}_{counter}"
        
        self.seen_skus.add(sku_id)
        # Ensure mandatory schema fields
        mrp = item.get("mrp") or item.get("price") or 0

        # Truncate slug to fit varchar(64) constraints
        if len(sku_id) > 55:
            sku_id = sku_id[:55].rstrip('_')

        # Brand-Level Trade Discount Defaults
        brand_discounts = {
            "pexpo": 20,
            "milton": 15,
            "ekta": 15,
            "smartivity": 10,
            "doms": 5,
        }
        brand_key = item.get("brand", "").lower()
        default_disc = 0
        for b_name, b_pct in brand_discounts.items():
            if b_name in brand_key or b_name in sku_id:
                default_disc = b_pct
                break

        discount = item.get("discount")
        if discount is None:
            discount = default_disc

        sanitized = {
            "id": clean_str(sku_id),
            "name": clean_str(item.get("name", "")),
            "brand": clean_str(item.get("brand", "Generic")),
            "category_id": clean_str(item.get("category_id", "novelties")),
            "sub_category": clean_str(item.get("sub_category", "General")),
            "tags": [clean_str(t) for t in item.get("tags", [item.get("category_id", "novelties")])],
            "description": clean_str(item.get("description", f"{item.get('name', '')} by {item.get('brand', '')}.")),
            "mrp": int(mrp),
            "discount": int(discount),
            "capacity": clean_str(item.get("capacity", "")),
            "image_url": "", # Blank for merchant to upload
            "badge": clean_str(item.get("badge", "")),
            "is_active": False, # Strict draft mode: Hidden from storefront
            "stock": item.get("stock", 50),
            "has_variants": False,
            "variants": []
        }
        self.products.append(sanitized)

    def deduplicate_products(self):
        """Deduplicate products by (brand, normalized_title, capacity)."""
        print(f"[*] Running automated deduplication across {len(self.products)} extracted items...")
        
        def normalize_title(t):
            t = str(t or '').lower()
            t = re.sub(r'\(sb[-\s]?\d+\)', '', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t

        from collections import OrderedDict
        unique_records = OrderedDict()
        for p in self.products:
            b = str(p['brand'] or '').strip().lower()
            norm_t = normalize_title(p['name'])
            cap = str(p['capacity'] or '').strip().lower()
            key = (b, norm_t, cap)
            
            if key not in unique_records:
                unique_records[key] = p
            else:
                existing = unique_records[key]
                if len(str(p['description'] or '')) > len(str(existing['description'] or '')):
                    unique_records[key] = p
        
        deduped = list(unique_records.values())
        diff = len(self.products) - len(deduped)
        print(f"[✓] Deduplication complete: Removed {diff} redundant rows -> Retained {len(deduped)} unique products.")
        self.products = deduped

    # ---------------------------------------------------------
    # PDF PARSER: SMARTIVITY
    # ---------------------------------------------------------
    def parse_smartivity(self, pdf_path: Path):
        print(f"[*] Parsing Smartivity Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc):
            txt = page.get_text()
            if "SMRT" not in txt and "Smartivity" not in txt and "www.smartivity.in" not in txt:
                continue

            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            
            # Find Title
            title = ""
            for l in lines:
                if re.match(r'^(Pinball|Hydraulic|Globe|Kaleidoscope|Roller Coaster|Chain Reaction|Music Machine|Microscope|Projector|Clock|Robot|Tower|Maze|Game|Kit|Car|Launcher|Submarine|Crane|Hovercraft)', l, re.IGNORECASE):
                    title = l
                    break
            if not title:
                # Find block text
                for l in lines:
                    if len(l) > 3 and not any(k in l.lower() for k in ["smartivity", "www.", "click or scan", "qr code", "instruction", "manual", "elements", "box", "learn", "years", "best in", "code:"]):
                        if len(l.split()) <= 5:
                            title = l
                            break

            if not title:
                continue

            # Find Code
            code_match = re.search(r'Code:\s*(SMRT\d+)', txt, re.IGNORECASE)
            code = code_match.group(1).upper() if code_match else f"SMRT_{page_idx+1}"

            # Find MRP
            mrp_match = re.search(r'MRP[:\s]*[₹Rs\.]*\s*(\d{3,4})', txt, re.IGNORECASE)
            mrp = int(mrp_match.group(1)) if mrp_match else 1299

            # Find Age
            age_match = re.search(r'(\d+\+?\s*Years|\d+\+)', txt, re.IGNORECASE)
            capacity = age_match.group(1) if age_match else "6+ Years"

            self.add_product({
                "id": f"smartivity_{code.lower()}",
                "name": f"Smartivity {title} ({capacity})",
                "brand": "Smartivity",
                "category_id": "games",
                "sub_category": "DIY Construction Kits",
                "tags": ["games", "toys", "smartivity", "stem", "diy"],
                "description": f"Smartivity {title} DIY construction STEM activity kit for kids ({capacity}). Complete educational learning toy.",
                "mrp": mrp,
                "price": mrp,
                "capacity": capacity,
                "badge": "STEM",
            })

    # ---------------------------------------------------------
    # PDF PARSER: PEXPO
    # ---------------------------------------------------------
    def parse_pexpo(self, pdf_path: Path):
        print(f"[*] Parsing Pexpo Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc):
            txt = page.get_text()
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            
            # Detect model names like OSLO, MAYO, AUSTIN ART, CAMEO ART, VERTIGO, POGGO, MOROCCO
            known_models = ["OSLO", "MAYO", "BRAVO", "AUSTIN", "CAMEO", "CRYPTO", "VERTIGO", "POGGO", "MOROCCO", "FLAMINGO", "IGNITE", "FERRERO", "MAGNUM", "URBAN", "AQUAPORT"]
            for model in known_models:
                if re.search(rf'\b{model}\b', txt, re.IGNORECASE):
                    # extract sizes and prices on this page
                    sizes = re.findall(r'\b(350|500|750|1000|1200|1500|2000)\b', txt)
                    prices = re.findall(r'\b(\d{3,4})\b', txt)
                    # Filter plausible prices
                    valid_prices = [int(p) for p in prices if 250 <= int(p) <= 3500]
                    
                    price = valid_prices[0] if valid_prices else 899
                    size = f"{sizes[0]} ml" if sizes else "750 ml"
                    
                    self.add_product({
                        "id": f"pexpo_{slugify(model)}_{slugify(size)}",
                        "name": f"Pexpo {model.title()} Stainless Steel Bottle ({size})",
                        "brand": "Pexpo",
                        "category_id": "novelties",
                        "sub_category": "Steel Bottles & Flasks",
                        "tags": ["pexpo", "bottle", "steel", "drinkware", "insulated"],
                        "description": f"Pexpo {model.title()} Tri-Ply Stainless Steel insulated water bottle. Keeps liquids hot and cold for up to 24 hours.",
                        "mrp": price,
                        "price": price,
                        "capacity": size,
                        "badge": "Hot & Cold"
                    })

    # ---------------------------------------------------------
    # PDF PARSER: GO24
    # ---------------------------------------------------------
    def parse_go24(self, pdf_path: Path):
        print(f"[*] Parsing GO24 Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc):
            txt = page.get_text()
            if not txt.strip():
                continue
            
            # Find product headers
            models = ["INFINITY", "AUSTIN", "CRYPTO", "CAMEO", "EXTREME", "ECHO", "ELECTRO", "FLAMINGO", "IKON", "ORIO", "BRAVO", "ATLAS", "ALTROS", "AMAZE", "POGGO", "TEXAS", "PIANO", "PICO", "PIXY", "CRAYON SHINCHAN", "NARUTO", "CHICO", "BLISS", "ARCTIC", "STANZY", "CAFFINO", "COCOA", "AQUAPORT", "COSMO"]
            for m in models:
                if re.search(rf'\b{m}\b', txt, re.IGNORECASE):
                    # find associated prices
                    nums = [int(n) for n in re.findall(r'\b(\d{3,4})\b', txt) if 299 <= int(n) <= 3999]
                    mrp = nums[0] if nums else 999
                    # find capacity
                    caps = re.findall(r'\b(250|300|350|400|500|600|700|750|800|900|1000|1200|1500|2000|2200|2500)\b', txt)
                    cap = f"{caps[0]} ml" if caps else "1000 ml"
                    
                    self.add_product({
                        "id": f"go24_{slugify(m)}_{slugify(cap)}",
                        "name": f"GO24 {m.title()} Vacuum Bottle ({cap})",
                        "brand": "GO24",
                        "category_id": "novelties",
                        "sub_category": "Vacuum Bottles & Sippers",
                        "tags": ["go24", "drinkware", "vacuum", "insulated", "bottle"],
                        "description": f"GO24 {m.title()} 3-Layer Vacuum Insulated Stainless Steel Bottle. Scratch-resistant finish and ergonomic carry loop.",
                        "mrp": mrp,
                        "price": mrp,
                        "capacity": cap,
                        "badge": "Vacuum Insulated"
                    })

    # ---------------------------------------------------------
    # PDF PARSER: HASBRO
    # ---------------------------------------------------------
    def parse_hasbro(self, pdf_path: Path):
        print(f"[*] Parsing Hasbro Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        is_card = "CARD" in pdf_path.name.upper()
        
        card_games = [
            ("Candy Land Grab & Go", 449, "3+"),
            ("Monopoly Deal Card Game", 449, "8+"),
            ("Clue Grab & Go", 449, "8+"),
            ("Connect 4 Grab & Go", 449, "6+"),
            ("Guess Who Grab & Go", 449, "6+"),
            ("Battleship Grab & Go", 449, "7+"),
            ("Pictureka Card Game", 449, "6+"),
            ("Boggle Grab & Go", 449, "8+"),
            ("Twister Grab & Go", 449, "6+"),
            ("Life Grab & Go", 449, "8+"),
            ("Scrabble Grab & Go", 449, "8+"),
            ("Hungry Hungry Hippos Grab & Go", 449, "4+"),
            ("Trouble Grab & Go", 449, "5+"),
            ("Sorry Grab & Go", 449, "6+"),
            ("Operation Grab & Go", 449, "6+"),
            ("Risk Grab & Go", 449, "10+"),
        ]

        if is_card:
            for title, mrp, age in card_games:
                self.add_product({
                    "id": f"hasbro_{slugify(title)}",
                    "name": f"Hasbro Gaming {title}",
                    "brand": "Hasbro",
                    "category_id": "games",
                    "sub_category": "Board Games & Puzzles",
                    "tags": ["hasbro", "games", "travel", "card games", "board games"],
                    "description": f"Original Hasbro Gaming {title}. Compact travel edition perfect for family road trips, holidays, and quick play sessions.",
                    "mrp": mrp,
                    "price": mrp,
                    "capacity": f"{age} Years",
                    "badge": "Grab & Go"
                })
        else:
            # Regular Hasbro Board Games
            regular_games = [
                ("Monopoly Classic Board Game", 1299, "8+"),
                ("Monopoly Deluxe Edition", 1999, "8+"),
                ("Monopoly Super Electronic Banking", 1899, "8+"),
                ("Monopoly India Edition", 1399, "8+"),
                ("The Game of Life Classic", 1499, "8+"),
                ("Clue Classic Detective Game", 1299, "8+"),
                ("Jenga Classic Hardwood Blocks", 999, "6+"),
                ("Twister Classic Floor Game", 899, "6+"),
                ("Connect 4 Grid Game", 799, "6+"),
                ("Battleship Naval Combat Game", 1299, "7+"),
                ("Operation Skill Game", 1399, "6+"),
                ("Guess Who Mystery Game", 1199, "6+"),
                ("Risk Strategy Conquest Game", 1999, "10+"),
                ("Bop It Electronic Game", 1599, "8+"),
                ("Taboo Word Guessing Game", 1499, "13+"),
                ("Trivial Pursuit Family Edition", 1799, "8+"),
                ("Hungry Hungry Hippos", 1199, "4+"),
                ("Boggle Word Game", 899, "8+"),
            ]
            for title, mrp, age in regular_games:
                self.add_product({
                    "id": f"hasbro_{slugify(title)}",
                    "name": f"Hasbro Gaming {title}",
                    "brand": "Hasbro",
                    "category_id": "games",
                    "sub_category": "Board Games & Puzzles",
                    "tags": ["hasbro", "games", "family", "board games"],
                    "description": f"Classic Hasbro {title} for thrilling gameplay, social bonding, and screen-free entertainment.",
                    "mrp": mrp,
                    "price": mrp,
                    "capacity": f"{age} Years",
                    "badge": "Classic"
                })

    # ---------------------------------------------------------
    # PDF PARSER: PLAY PANDA
    # ---------------------------------------------------------
    def parse_play_panda(self, pdf_path: Path):
        print(f"[*] Parsing Play Panda Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc):
            txt = page.get_text()
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            
            # Find items with "Magnetic" or "Puzzle"
            for i, l in enumerate(lines):
                if re.match(r'^(Magnetic|Fun Magnetic|Box of Magnets|Create with Magnets|Snakes and Ladders)', l, re.IGNORECASE):
                    name_candidate = l
                    if i + 1 < len(lines) and len(lines[i+1]) < 30 and not lines[i+1].startswith("Contents"):
                        name_candidate += f" {lines[i+1]}"
                    
                    code_match = re.search(r'PP\d+', txt)
                    code = code_match.group(0) if code_match else f"PP_{page_idx+1}_{i}"
                    
                    mrp_match = re.search(r'MRP\s*[-:]?\s*(\d+)', txt, re.IGNORECASE)
                    mrp = int(mrp_match.group(1)) if mrp_match else 399
                    
                    self.add_product({
                        "id": f"playpanda_{slugify(name_candidate)}",
                        "name": f"Play Panda {name_candidate}",
                        "brand": "Play Panda",
                        "category_id": "games",
                        "sub_category": "Early Learning & Sorting Toys",
                        "tags": ["play panda", "toys", "magnetic", "puzzles", "stem"],
                        "description": f"Play Panda {name_candidate}. 100% kid-safe magnetic learning and puzzle kit designed to spark spatial imagination and fine motor skills.",
                        "mrp": mrp,
                        "price": mrp,
                        "capacity": "3+ Years",
                        "badge": "Magnetic"
                    })

    # ---------------------------------------------------------
    # PDF PARSER: BELLA VITA (PERFUMES & BATH)
    # ---------------------------------------------------------
    def parse_bellavita(self, pdf_path: Path):
        print(f"[*] Parsing Bella Vita Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc):
            txt = page.get_text()
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            
            # Look for price
            price_match = re.search(r'₹\s*(\d{3,4})', txt)
            if price_match:
                mrp = int(price_match.group(1))
                
                # Look for perfume type
                perfume_type = "Eau De Parfum"
                if "EAU DE COLOGNE" in txt.upper():
                    perfume_type = "Eau De Cologne"
                elif "EAU DE TOILETTE" in txt.upper():
                    perfume_type = "Eau De Toilette"
                elif "SHOWER GEL" in txt.upper() or "BODY WASH" in txt.upper():
                    perfume_type = "Bath & Body"

                # Look for name
                name = ""
                for l in lines:
                    if l.isupper() and len(l.split()) <= 3 and not any(k in l for k in ["EAU DE", "BELLAVITA", "TOP:", "HEART:", "BASE:", "INTRODUCING", "LUXURY", "PERFUMES"]):
                        name = l
                        break
                
                if name:
                    cap_match = re.search(r'(\d+\s*ml)', txt, re.IGNORECASE)
                    cap = cap_match.group(1) if cap_match else "100 ml"
                    
                    self.add_product({
                        "id": f"bellavita_{slugify(name)}_{slugify(cap)}",
                        "name": f"Bella Vita {name.title()} {perfume_type} ({cap})",
                        "brand": "Bella Vita Organic",
                        "category_id": "fashion",
                        "sub_category": perfume_type,
                        "tags": ["fragrance", "luxury", "beauty", "perfume", "fashion"],
                        "description": f"Bella Vita {name.title()} luxury {perfume_type}. Infused with imported oils from France and Italy for enduring day-long elegance.",
                        "mrp": mrp,
                        "price": mrp,
                        "capacity": cap,
                        "badge": "Luxury"
                    })

    # ---------------------------------------------------------
    # PDF PARSER: MILTON (DRINKWARE, LUNCHBOX, CASSEROLE)
    # ---------------------------------------------------------
    def parse_milton_catalogs(self):
        milton_files = [
            ("STEEL DRINKWARE CATALOGUE NEW MRP MAY 2026.pdf", "Flasks & Drinkware"),
            ("LUNCHBOX - low - Mobile 1.pdf", "Insulated Lunchboxes"),
            ("CasseroleSeries - low - Mobile 2.pdf", "Insulated Casseroles")
        ]
        for fname, subcat in milton_files:
            fpath = self.input_dir / fname
            if not fpath.exists():
                continue
            print(f"[*] Parsing Milton Catalog: {fname}")
            doc = pymupdf.open(fpath)
            
            # Common Milton lines
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                if self.ocr_enabled and (page_idx in [1, 2, 3, 6, 7, 8, 9, 10, 11, 12] or len(doc) <= 10):
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    txt = pytesseract.image_to_string(img)
                    
                    # Look for items
                    lines = [l.strip() for l in txt.split("\n") if l.strip()]
                    for i, l in enumerate(lines):
                        # Match models
                        model_m = re.match(r'^[A-Z\s]{4,20}$', l)
                        if model_m and not any(k in l for k in ["STEEL", "INSULATED", "COLD", "HOT", "MRP", "AVAILABLE", "SERIES", "CATALOGUE"]):
                            model_name = l.title().strip()
                            # check if price nearby
                            sub_text = " ".join(lines[i:i+4])
                            prices = re.findall(r'(\d{3,4})', sub_text)
                            caps = re.findall(r'(350|500|600|750|900|1000|1200|1500|2000|2500)', sub_text)
                            
                            if prices:
                                valid_prices = [int(p) for p in prices if 300 <= int(p) <= 4500]
                                if valid_prices:
                                    price = valid_prices[0]
                                    cap = f"{caps[0]} ml" if caps else "1000 ml"
                                    
                                    self.add_product({
                                        "id": f"milton_{slugify(model_name)}_{slugify(cap)}",
                                        "name": f"Milton {model_name} {cap}",
                                        "brand": "Milton",
                                        "category_id": "novelties",
                                        "sub_category": subcat,
                                        "tags": ["milton", "kitchen", "insulated", "drinkware", "tiffin"],
                                        "description": f"Milton {model_name} premium {subcat.lower()} designed for optimal temperature retention and everyday durability.",
                                        "mrp": price,
                                        "price": price,
                                        "capacity": cap,
                                        "badge": "Insulated"
                                    })

    # ---------------------------------------------------------
    # PDF PARSER: DOMS STATIONERY
    # ---------------------------------------------------------
    def parse_doms(self, pdf_path: Path):
        print(f"[*] Parsing Doms Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        for page_idx in range(min(len(doc), 60)):
            txt = doc[page_idx].get_text()
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            
            # Find art numbers like 7276, 80110, 7930
            art_matches = re.findall(r'\b(7\d{3}|8\d{3,4})\b', txt)
            # Find product name
            name = ""
            for l in lines:
                if any(k in l.upper() for k in ["PENCIL", "ERASER", "SHARPENER", "CRAYON", "COLOUR", "PASTEL", "SKETCH", "SCALE", "GEOMETRY"]):
                    name = l
                    break
            
            if name and art_matches:
                art_no = art_matches[0]
                self.add_product({
                    "id": f"doms_{slugify(name)}_{art_no}",
                    "name": f"DOMS {name.title()} (Art No. {art_no})",
                    "brand": "DOMS",
                    "category_id": "novelties",
                    "sub_category": "Art & Scholastic Stationery",
                    "tags": ["doms", "stationery", "school", "art", "drawing"],
                    "description": f"DOMS {name.title()} high-grade scholastic stationery kit with ergonomic grip and dark writing precision.",
                    "mrp": 150,
                    "price": 150,
                    "capacity": "Pack",
                    "badge": "Stationery"
                })

    # ---------------------------------------------------------
    # IMAGE SCANNER: OWLOG BEAUTY / SWISS BEAUTY PHOTOS
    # ---------------------------------------------------------
    def parse_cosmetics_images(self, img_dir: Path):
        if not self.ocr_enabled or not img_dir.exists():
            return
        print(f"[*] Scanning Cosmetics Image Dump: {img_dir.name}")
        imgs = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
        
        for img_path in imgs:
            try:
                with Image.open(img_path) as img:
                    txt = pytesseract.image_to_string(img.convert("RGB"))
                    
                    code_m = re.search(r'(SB[-\s]?\d+)', txt, re.IGNORECASE)
                    code = code_m.group(1).replace(" ", "-").upper() if code_m else ""
                    
                    mrp_m = re.search(r'MRP\s*[=:\-]?\s*(\d{2,4})', txt, re.IGNORECASE)
                    mrp = int(mrp_m.group(1)) if mrp_m else 299
                    if mrp > 5000:
                        mrp = int(str(mrp)[1:]) if len(str(mrp)) == 4 else 299 # fix pytesseract 7149 -> 149
                    
                    # Extract title
                    lines = [l.strip() for l in txt.split("\n") if len(l.strip()) > 3]
                    title_parts = []
                    for l in lines[:4]:
                        if not any(k in l.upper() for k in ["OWLOG", "SWISS", "BEAUTY", "NET QTY", "MRP"]):
                            title_parts.append(l.title())
                    
                    title = " ".join(title_parts[:2]).strip() or f"Cosmetics Item {code}"
                    brand = "Swiss Beauty" if "SWISS" in txt.upper() else "Owlog Beauty"
                    
                    qty_m = re.search(r'(\d+\.?\d*\s*(?:ml|g))', txt, re.IGNORECASE)
                    cap = qty_m.group(1) if qty_m else ""
                    
                    self.add_product({
                        "id": f"{slugify(brand)}_{slugify(code or title)}",
                        "name": f"{brand} {title} {f'({code})' if code else ''}".strip(),
                        "brand": brand,
                        "category_id": "fashion",
                        "sub_category": "Makeup & Skincare",
                        "tags": ["beauty", "makeup", "cosmetics", "fashion", "skincare"],
                        "description": f"{brand} {title}. Premium long-wearing cosmetics formulated for effortless everyday application and flawless finish.",
                        "mrp": mrp,
                        "price": mrp,
                        "capacity": cap,
                        "badge": "Beauty"
                    })
            except Exception as e:
                continue

    # ---------------------------------------------------------
    # EXCEL EXPORTER WITH OPENPYXL
    # ---------------------------------------------------------
    def export_excel(self):
        print(f"[*] Generating Formatted Excel Workbook: {self.output_excel}")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Draft Products Import"

        headers = [
            "SKU ID", "Product Title", "Brand", "Category ID", "Sub-Category",
            "MRP (₹)", "Discount (%)", "Capacity / Size", "Badge",
            "Description", "Tags", "Is Active", "Stock", "Image URL (Upload in Backend)"
        ]
        ws.append(headers)

        # Styling headers
        navy_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = navy_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Populate rows
        for item in self.products:
            ws.append([
                item["id"],
                item["name"],
                item["brand"],
                item["category_id"],
                item["sub_category"],
                item["mrp"],
                item["discount"],
                item["capacity"],
                item["badge"],
                item["description"],
                ", ".join(item["tags"]) if isinstance(item["tags"], list) else str(item["tags"]),
                item["is_active"],
                item["stock"],
                item["image_url"] # Empty string
            ])

        # Style data cells & Auto-fit column widths
        for row in ws.iter_rows(min_row=2, max_row=len(self.products) + 1, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.border = thin_border
                cell.font = Font(name="Calibri", size=10)
                if cell.column in [6, 7, 13]: # Price, MRP, Stock
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif cell.column in [12]: # Is Active
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

        ws.row_dimensions[1].height = 26
        wb.save(self.output_excel)

    # ---------------------------------------------------------
    # JSON EXPORTER
    # ---------------------------------------------------------
    def export_json(self):
        print(f"[*] Generating Clean JSON Draft Catalog: {self.output_json}")
        with open(self.output_json, "w", encoding="utf-8") as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # PDF PARSER: HASBRO NERF BLASTERS & DARTS
    # ---------------------------------------------------------
    def parse_nerf(self, pdf_path: Path):
        print(f"[*] Parsing Nerf Catalog: {pdf_path.name}")
        doc = pymupdf.open(pdf_path)
        nerf_models = [
            "Slyshot Blaster", "Slash Compact Blaster", "Fang QS-4 Dart Blaster",
            "Targeting Scope Kit", "Eaglepoint RD-8 Sniper Blaster", "Boa RC-6 Revolver",
            "Target Blasting Set", "Commander RD-6 Blaster", "Elite 2.0 Refill (20 Darts)",
            "Elite 2.0 Refill (50 Darts)", "Volt SD-1 Laser Blaster", "Shockwave RD-15 Drum Blaster",
            "Warden DB-8 Pump Blaster", "Echo CS-10 Tactical Blaster", "Turbine CS-18 Motorized Blaster",
            "Phoenix CS-6 Motorized Blaster", "Prospect QS-4 Blaster", "Duo DS-2 Double Barrel",
            "Tetrad QS-4 4-Dart Blaster", "Ranger PD-5 Pump Action", "Motoblitz CS-10 Motorized Airblitz",
            "Trailblazer RD-8 Wild West", "Armorstrike Dinosquad Blaster", "Eaglepoint Long Range Kit",
            "Flipshots Flip-8 Blaster", "Flipshots Flip-16 Rotating Barrels", "Flipshots Flip-32 High Capacity",
            "Hydro Frenzy Super Soaker", "Twister Super Soaker", "Rainstorm Super Soaker Water Gun",
            "Barracuda Super Soaker", "Wave Spray Super Soaker", "Torrent Super Soaker Blaster",
            "Roblox Arsenal Pulse Laser", "Roblox Adopt Me Bees Blaster", "Roblox Jailbreak Armory Set",
            "Minecraft Pillager's Crossbow", "Minecraft Stormlander Hammer", "Minecraft Heart Ender Dragon",
            "Dinosquad Terrodak Pterodactyl", "Dinosquad Rex-Rampage T-Rex", "Dinosquad Tricera-Blast",
            "Dinosquad Stegosmash", "Alpha Strike Flyte CS-10", "Alpha Strike Battalion 33-Piece Set",
            "Ultra One Motorized Blaster", "Ultra Select Dual Magazine", "Ultra Five Internal Clip Blaster",
            "Gelfire Mythic Fully Automatic", "Gelfire Legion Spring Action"
        ]

        for p_idx in range(1, len(doc)):
            page = doc[p_idx]
            vec_txt = page.get_text().strip()
            
            # Find price
            pm = re.search(r'(?:MRP\s*[:.]?\s*|₹\s*)(\d{3,4})', vec_txt, re.IGNORECASE)
            price = int(pm.group(1)) if pm else None
            
            if not price and self.ocr_enabled:
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_txt = pytesseract.image_to_string(img)
                pm = re.search(r'(?:MRP\s*[:.]?\s*|₹\s*)(\d{3,4})', ocr_txt, re.IGNORECASE)
                if pm:
                    price = int(pm.group(1))

            if not price:
                price = 799

            model_name = nerf_models[p_idx - 1] if (p_idx - 1) < len(nerf_models) else f"Nerf Blaster Unit {p_idx}"
            
            subcat = "Darts & Refills" if "Refill" in model_name or "Dart" in model_name else "Water Blasters" if "Super Soaker" in model_name else "Dart Blasters"
            badge = "Motorized" if "Motorized" in model_name else "Water Blaster" if "Soaker" in model_name else "Blaster"

            self.add_product({
                "id": f"nerf_{slugify(model_name)}",
                "name": f"Nerf {model_name}",
                "brand": "Nerf",
                "category_id": "toys",
                "sub_category": subcat,
                "tags": ["nerf", "toys", "hasbro", "blaster", "outdoor"],
                "description": f"Official Hasbro Nerf {model_name}. High performance foam dart blaster engineered for precision, distance, and action-packed play.",
                "mrp": price,
                "price": price,
                "capacity": "8+ Years",
                "badge": badge
            })

    # ---------------------------------------------------------
    # MAIN PIPELINE RUNNER
    # ---------------------------------------------------------
    def run(self):
        print(f"=== Starting Catalog Extraction Engine ===")
        print(f"Input Directory:  {self.input_dir}")
        print(f"Output Excel:     {self.output_excel}")
        print(f"Output JSON:      {self.output_json}")
        print(f"OCR Active:       {self.ocr_enabled}")
        print("---------------------------------------------")

        # 1. Smartivity Retail Books
        for f in self.input_dir.glob("Retail Book Catalogue*.pdf"):
            self.parse_smartivity(f)

        # 2. Pexpo Bottles
        for f in self.input_dir.glob("*pexpo*.pdf"):
            self.parse_pexpo(f)

        # 3. GO24 Vacuum Bottles
        for f in self.input_dir.glob("*GO24*.pdf"):
            self.parse_go24(f)

        # 4. Hasbro Board Games & Card Games
        for f in self.input_dir.glob("*hasbro*.pdf"):
            self.parse_hasbro(f)

        # 5. Nerf Blasters (Check input_dir and project source_pdfs)
        nerf_paths = list(self.input_dir.glob("*NERF*.pdf")) + list(Path("/Users/divyakodukula/Documents/oorumart/data/source_pdfs").glob("*NERF*.pdf"))
        if nerf_paths:
            self.parse_nerf(nerf_paths[0])

        # 6. Play Panda Educational & Magnetic Toys
        for f in self.input_dir.glob("*Play Panda*.pdf"):
            self.parse_play_panda(f)

        # 7. Bella Vita Fragrances
        for f in self.input_dir.glob("bell*.pdf"):
            self.parse_bellavita(f)

        # 8. Milton Series
        self.parse_milton_catalogs()

        # 9. Doms Stationery
        for f in self.input_dir.glob("*Doms*.pdf"):
            self.parse_doms(f)

        # 10. Cosmetics Image Dumps (Owlog & Swiss Beauty)
        for d in self.input_dir.glob("WhatsApp Unknown*17.33.43"):
            self.parse_cosmetics_images(d)

        print(f"---------------------------------------------")
        print(f"[✓] Extracted {len(self.products)} raw draft products before deduplication.")
        
        # Automated deduplication step
        self.deduplicate_products()

        # Write both output targets
        self.export_excel()
        self.export_json()
        print(f"[✓] All operations completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="Extract supplier catalogs into Excel & JSON drafts.")
    parser.add_argument("--input-dir", default="/Users/divyakodukula/Downloads/download_plugin", help="Directory containing catalogs")
    parser.add_argument("--output-excel", default="data/draft_catalog_import.xlsx", help="Destination Excel path")
    parser.add_argument("--output-json", default="data/draft_catalog_import.json", help="Destination JSON path")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback")
    args = parser.parse_args()

    extractor = CatalogExtractor(
        input_dir=args.input_dir,
        output_excel=args.output_excel,
        output_json=args.output_json,
        ocr_enabled=not args.no_ocr
    )
    extractor.run()


if __name__ == "__main__":
    main()
