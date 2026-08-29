#!/usr/bin/env python3
"""
scripts/update_shop_theme_colors.py

Updates Supabase Cloud DB theme colors for 'yesfancy':
- primary_color: '#0F172A' (Deep Slate)
- secondary_color: '#D4AF37' (Warm Gold)
- accent_color: '#E63946' (Coral Red)
"""

import os
import dotenv
from supabase import create_client

dotenv.load_dotenv()

def update_theme():
    print("🚀 Updating Theme Colors in Supabase Cloud DB for 'yesfancy'...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)

    res = supabase.table('shops').update({
        'theme': {
            'primary_color': '#0F172A',
            'secondary_color': '#D4AF37',
            'accent_color': '#E63946',
            'font_title': 'Playfair Display',
            'font_body': 'Plus Jakarta Sans'
        }
    }).eq('slug', 'yesfancy').execute()

    print("  ✅ Supabase DB Updated: 'shops.theme' set to Deep Slate (#0F172A) & Gold (#D4AF37)")

if __name__ == '__main__':
    update_theme()
