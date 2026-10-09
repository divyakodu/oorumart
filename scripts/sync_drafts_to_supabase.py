#!/usr/bin/env python3
"""
scripts/sync_drafts_to_supabase.py
----------------------------------
Appends newly extracted draft catalog entries into master_catalog.json
and synchronizes them directly into Supabase Cloud Database under YesFancy.

Guarantees:
- Never duplicates existing entries (checks product ID uniqueness).
- Sets is_active = False on all new drafts (draft safety on storefront).
- Upserts batches safely to Supabase via REST API.
"""

import os
import json
import ssl
import urllib.request
import urllib.error

SHOP_ID = "8ca39196-2948-4d61-bfe2-388875120b2b" # YesFancy
DRAFT_JSON_PATH = "data/draft_catalog_import.json"
MASTER_JSON_PATHS = [
    "src/data/master_catalog.json",
    "data/master_catalog.json"
]

def load_env():
    env_vars = {}
    for env_file in ['.env', '.env.local', '.env.production']:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def main():
    print("=== Appending Drafts to Master Catalog & Supabase ===")
    
    env = load_env()
    supabase_url = env.get("PUBLIC_SUPABASE_URL", "https://fwrievuhudjkeffmszqf.supabase.co")
    service_key = env.get("SUPABASE_SERVICE_ROLE_KEY", env.get("PUBLIC_SUPABASE_ANON_KEY"))
    
    if not service_key:
        print("❌ Error: Supabase credentials not found in environment.")
        return

    # 1. Read Draft JSON
    with open(DRAFT_JSON_PATH, "r", encoding="utf-8") as f:
        draft_products = json.load(f)
    print(f"[*] Loaded {len(draft_products)} draft products from {DRAFT_JSON_PATH}")

    # 2. Append to Master Catalog JSON files safely
    for mpath in MASTER_JSON_PATHS:
        if not os.path.exists(mpath):
            continue
        with open(mpath, "r", encoding="utf-8") as f:
            master = json.load(f)
        
        master_ids = set(p["id"] for p in master)
        to_append = [p for p in draft_products if p["id"] not in master_ids]
        
        if to_append:
            master.extend(to_append)
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(master, f, indent=2, ensure_ascii=False)
            print(f"[✓] Appended {len(to_append)} items to {mpath} (Total now: {len(master)})")
        else:
            print(f"[-] No new items to append to {mpath} (already present)")

    # 3. Synchronize with Supabase Cloud DB
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    db_rows = []
    for p in draft_products:
        db_rows.append({
            "id": p["id"],
            "shop_id": SHOP_ID,
            "name": p["name"],
            "description": p.get("description", ""),
            "price": float(p.get("price", 0)),
            "mrp": float(p.get("mrp", p.get("price", 0))),
            "category_id": p.get("category_id", "novelties"),
            "badge": p.get("badge") or None,
            "tags": p.get("tags") if isinstance(p.get("tags"), list) else [p.get("category_id", "novelties")],
            "image_url": p.get("image_url", ""),
            "stock": int(p.get("stock", 50)),
            "is_active": False # Strict draft mode: Hidden from storefront
        })

    print(f"[*] Prepared {len(db_rows)} rows for Supabase upsert...")

    batch_size = 50
    total_upserted = 0
    for i in range(0, len(db_rows), batch_size):
        chunk = db_rows[i:i + batch_size]
        url = f"{supabase_url}/rest/v1/products?on_conflict=shop_id,id"
        req = urllib.request.Request(
            url,
            data=json.dumps(chunk).encode("utf-8"),
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                total_upserted += len(chunk)
                print(f"  ✓ Upserted Supabase batch {i//batch_size + 1} ({len(chunk)} items) - Total: {total_upserted}/{len(db_rows)}")
        except urllib.error.HTTPError as e:
            print(f"  ❌ Error upserting batch {i//batch_size + 1}: {e.code} - {e.read().decode('utf-8')}")

    print(f"\n[✓] Cloud synchronization complete! Total upserted: {total_upserted} draft items.")

if __name__ == "__main__":
    main()
