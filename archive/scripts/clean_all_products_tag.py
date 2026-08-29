#!/usr/bin/env python3
"""
scripts/clean_all_products_tag.py

Updates Supabase DB categories table for shop 'yesfancy':
1. Sets label for 'all' to 'All Products' (clean, zero emojis, zero long text).
2. Cleans any remaining emoji from all categories.
"""

import os
import dotenv
import re
from supabase import create_client

dotenv.load_dotenv()

def clean_tags():
    print("🚀 Cleaning All Products Tag in Supabase Cloud DB...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)
    shop_res = supabase.table('shops').select('id').eq('slug', 'yesfancy').single().execute()
    shop_id = shop_res.data['id']

    # 1. Update or upsert 'all' category
    cats_res = supabase.table('categories').select('*').eq('shop_id', shop_id).execute()
    existing_cats = cats_res.data or []

    for c in existing_cats:
        raw_label = c.get('label', '')
        # Remove any non-alphanumeric leading symbols/emojis
        clean_label = re.sub(r'^[^\w\s]+\s*', '', raw_label).strip()
        if c.get('id') == 'all' or c.get('category_id') == 'all':
            clean_label = 'All Products'

        supabase.table('categories').update({'label': clean_label}).eq('shop_id', shop_id).eq('id', c['id']).execute()
        print(f"  ✅ Updated Category '{c['id']}' -> '{clean_label}'")

    print("\n🎉 SUPABASE DB UPDATE COMPLETE: 'All Products' tag updated!")

if __name__ == '__main__':
    clean_tags()
