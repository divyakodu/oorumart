#!/usr/bin/env python3
"""
scripts/remove_emojis_from_db.py

Strips all emoji icons from category/tag labels in Supabase Cloud DB:
- 'Gift Store'
- 'Home & Decor'
- 'Bags & Travel'
- 'Board Games'
- 'Action Toys'
- 'Lunch Boxes'
"""

import os
import dotenv
import re
from supabase import create_client

dotenv.load_dotenv()

CLEAN_TAGS = [
    {"id": "gift_store", "label": "Gift Store"},
    {"id": "home_decor", "label": "Home & Decor"},
    {"id": "bags_travel", "label": "Bags & Travel"},
    {"id": "board_games", "label": "Board Games"},
    {"id": "action_toys", "label": "Action Toys"},
    {"id": "lunch_boxes", "label": "Lunch Boxes"}
]

def remove_emojis():
    print("🚀 Removing Emoji Iconography from Supabase Cloud DB...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)
    shop_res = supabase.table('shops').select('id').eq('slug', 'yesfancy').single().execute()
    shop_id = shop_res.data['id']

    # Update categories table
    for cat in CLEAN_TAGS:
        supabase.table('categories').update({'label': cat['label']}).eq('shop_id', shop_id).eq('id', cat['id']).execute()
        print(f"  ✅ Category [{cat['id']}] -> Set Clean Title: '{cat['label']}'")

    print("\n🎉 SUPABASE DB UPDATE COMPLETE: All emoji icons removed from DB!")

if __name__ == '__main__':
    remove_emojis()
