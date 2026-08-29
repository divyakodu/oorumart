#!/usr/bin/env python3
"""
scripts/update_yesfancy_logo.py

Updates logo_url in Supabase Cloud DB for shop 'yesfancy' to '/images/yes_fancy_logo.png'
"""

import os
import dotenv
from supabase import create_client

dotenv.load_dotenv()

def update_logo():
    print("🚀 Updating Yes Fancy Logo URL in Supabase Cloud DB...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)
    res = supabase.table('shops').update({
        'logo_url': '/images/yes_fancy_logo.png'
    }).eq('slug', 'yesfancy').execute()

    print("  ✅ Supabase DB Updated: 'shops.logo_url' set to '/images/yes_fancy_logo.png'")

if __name__ == '__main__':
    update_logo()
