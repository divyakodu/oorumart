#!/usr/bin/env python3
"""
Synchronize tags and badges for all Bella Vita Beauty & Lifestyle products in
Supabase Cloud DB and master_catalog.json.
Ensures that all fragrance and gift sets are tagged with 'gifts' and given proper badges.
"""

import os
import json
import urllib.request
import ssl
from dotenv import load_dotenv

load_dotenv("/Users/divyakodukula/Documents/oorumart/.env")

SHOP_ID = "8ca39196-2948-4d61-bfe2-388875120b2b"
SUPABASE_URL = os.environ.get("PUBLIC_SUPABASE_URL", "https://fwrievuhudjkeffmszqf.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

MASTER_CATALOG_PATHS = [
    "/Users/divyakodukula/Documents/oorumart/src/data/master_catalog.json",
    "/Users/divyakodukula/Documents/oorumart/data/master_catalog.json"
]

def determine_tags_and_badge(name, sub_category, slug):
    name_lower = name.lower()
    sub_lower = sub_category.lower()

    if "gift set" in name_lower or "combo" in name_lower or "gift set" in sub_lower:
        tags = ["gifts", "gift set", "beauty", "lifestyle", "perfume", "fragrance", "luxury"]
        badge = "GIFT SET"
    elif "pocket perfume" in name_lower or "20ml" in name_lower:
        tags = ["gifts", "pocket perfume", "beauty", "lifestyle", "fragrance", "travel"]
        badge = "TRAVEL SIZE"
    elif "eau de parfum" in name_lower or "eau de cologne" in name_lower or "eau de toilette" in name_lower:
        tags = ["gifts", "beauty", "lifestyle", "perfume", "fragrance", "luxury", "eau de parfum"]
        badge = "LUXURY"
    elif "deo" in name_lower or "deo" in sub_lower:
        tags = ["beauty", "lifestyle", "deodorant", "fragrance", "personal care", "no gas"]
        badge = "NO GAS DEO"
    elif "body mist" in name_lower or "mist" in sub_lower:
        tags = ["gifts", "beauty", "lifestyle", "body mist", "fragrance", "personal care"]
        badge = "BODY MIST"
    elif "shower gel" in name_lower:
        tags = ["beauty", "lifestyle", "shower gel", "bath and body", "personal care"]
        badge = "BATH & BODY"
    elif "bathing bar" in name_lower or "soap" in name_lower:
        tags = ["gifts", "beauty", "lifestyle", "soap", "bath and body", "personal care"]
        badge = "PACK OF 3"
    elif "face wash" in name_lower:
        tags = ["beauty", "lifestyle", "face wash", "skincare", "cleanser", "personal care"]
        badge = "FACE WASH"
    elif "body lotion" in name_lower or "lotion" in sub_lower:
        tags = ["beauty", "lifestyle", "body lotion", "skincare", "moisturizer", "personal care"]
        badge = "BODY LOTION"
    elif "sunscreen" in name_lower:
        tags = ["beauty", "lifestyle", "sunscreen", "skincare", "spf 50", "personal care"]
        badge = "SUNSCREEN"
    else:
        tags = ["gifts", "beauty", "lifestyle", "perfume", "fragrance"]
        badge = "BEAUTY"

    return tags, badge

def main():
    print("=" * 60)
    print("✨ SYNCHRONIZING BEAUTY & LIFESTYLE TAGS & BADGES")
    print("=" * 60)

    # 1. Update Master Catalog JSONs
    for cat_path in MASTER_CATALOG_PATHS:
        if not os.path.exists(cat_path):
            continue
        with open(cat_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        updated_count = 0
        gift_count = 0
        for item in catalog:
            if str(item.get("id", "")).startswith("bellavita_"):
                tags, badge = determine_tags_and_badge(
                    item.get("name", ""),
                    item.get("sub_category", ""),
                    item.get("id", "")
                )
                item["tags"] = tags
                item["badge"] = badge
                updated_count += 1
                if "gifts" in tags:
                    gift_count += 1

        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        print(f"✓ Updated {cat_path}: {updated_count} products updated ({gift_count} tagged with 'gifts')")

    # 2. Update Supabase Cloud DB
    print("\n☁️ Updating Supabase Cloud Database rows...")
    ctx = ssl._create_unverified_context()

    # Read the updated master catalog
    with open(MASTER_CATALOG_PATHS[0], "r", encoding="utf-8") as f:
        catalog = json.load(f)

    bv_items = [x for x in catalog if str(x.get("id", "")).startswith("bellavita_")]
    db_rows = []
    for c in bv_items:
        db_rows.append({
            "id": c["id"],
            "shop_id": SHOP_ID,
            "name": c["name"],
            "description": c["description"],
            "price": c["price"],
            "category_id": "fashion",
            "image_url": c["image_url"],
            "stock": c["stock"],
            "badge": c["badge"],
            "tags": c["tags"],
            "is_active": True
        })

    batch_size = 50
    for i in range(0, len(db_rows), batch_size):
        chunk = db_rows[i:i + batch_size]
        upsert_req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/products?on_conflict=shop_id,id",
            data=json.dumps(chunk).encode("utf-8"),
            headers={
                "apikey": SERVICE_KEY,
                "Authorization": f"Bearer {SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(upsert_req, context=ctx) as r:
                print(f"  ✓ Upserted Supabase batch {i//batch_size + 1} ({len(chunk)} items with tags & badges)")
        except urllib.error.HTTPError as e:
            print(f"  Error upserting batch: {e.code} - {e.read().decode('utf-8')}")

    print("\n🎉 Tags and badges successfully synchronized!")

if __name__ == "__main__":
    main()
