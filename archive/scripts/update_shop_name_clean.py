#!/usr/bin/env python3
"""
scripts/update_shop_name_clean.py

Updates shop name in Supabase Cloud DB for 'yesfancy':
- Sets name = 'Yes Fancy' (removing '& Gift Corner')
"""

import os
import dotenv
from supabase import create_client

dotenv.load_dotenv()

def update_shop_name():
    print("🚀 Updating Shop Name in Supabase Cloud DB to 'Yes Fancy'...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)

    res = supabase.table('shops').update({
        'name': 'Yes Fancy'
    }).eq('slug', 'yesfancy').execute()

    print("  ✅ Supabase DB Updated: 'shops.name' set to 'Yes Fancy'")

if __name__ == '__main__':
    update_shop_name()
