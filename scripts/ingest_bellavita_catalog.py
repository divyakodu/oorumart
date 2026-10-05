#!/usr/bin/env python3
"""
Ingest Bella Vita Luxury Catalog (bell.pdf) and 95 high-resolution product screenshots.
Converts screenshot PNGs to lightweight WebP (<60KB), generates master catalog entries,
appends to master_catalog.json, and synchronizes with Supabase Cloud Database.
"""

import os
import json
import re
from PIL import Image
import urllib.request
import ssl

from dotenv import load_dotenv
load_dotenv("/Users/divyakodukula/Documents/oorumart/.env")

SHOP_ID = "8ca39196-2948-4d61-bfe2-388875120b2b"
SUPABASE_URL = os.environ.get("PUBLIC_SUPABASE_URL", "https://fwrievuhudjkeffmszqf.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3cmlldnVodWRqa2VmZm1zenFmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDQyNzUwNCwiZXhwIjoyMDkwMDAzNTA0fQ.0ETTHks_RkOoQNtYRH3xhXQAKuvPOCGsgyHAlYWbaBI")


SCREENSHOTS_DIR = "/Users/divyakodukula/Documents/oorumart/experiments/screenshots"
OUTPUT_IMG_DIR = "/Users/divyakodukula/Documents/oorumart/public/images/products"
MASTER_CATALOG_PATHS = [
    "/Users/divyakodukula/Documents/oorumart/src/data/master_catalog.json",
    "/Users/divyakodukula/Documents/oorumart/data/master_catalog.json"
]

# Product Definitions (1-to-1 index matching sorted screenshots [0..94])
PRODUCTS = [
    # 01 - 04: Premium 100ml (Page 4)
    {
        "slug": "ocean_man_edp_100ml",
        "name": "Bella Vita Ocean Man Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Premium luxury fragrance for men. Top notes: Aldehydic, Aqueous, Fresh. Heart: Orchid, Ozonic, Floral. Base: Ambergris, Musk, Woody."
    },
    {
        "slug": "oud_gold_edp_100ml",
        "name": "Bella Vita Oud Gold Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Rich artisanal amber oud fragrance. Top: Caramel. Heart: Rose, Jasmine, and Orris. Base: Ambery Oud."
    },
    {
        "slug": "oud_dark_edp_100ml",
        "name": "Bella Vita Oud Dark Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Intense smoky oud fragrance for men and women. Top: Citrus and Grapefruit. Heart: Floral, Vetiver, and Orris. Base: Musky Oud."
    },
    {
        "slug": "ceo_man_intense_edp_100ml",
        "name": "Bella Vita CEO Man Intense Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Powerful executive fragrance. Top: Lavender and Bergamot. Heart: Carnation and Orchid. Base: Musk, Ambergris, and Patchouli."
    },
    # 05 - 07: Premium 100ml (Page 5)
    {
        "slug": "blu_man_edp_100ml",
        "name": "Bella Vita B.L.U. Man Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Aquatic fresh aromatic fragrance. Top: Lemon, Nutmeg, Mandarin and Black Pepper. Heart: Apple, Orris and Pineapple. Base: Musk, Vetiver, Amber and Moss."
    },
    {
        "slug": "diva_woman_edp_100ml",
        "name": "Bella Vita D.I.V.A Woman Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Enchanting feminine luxury perfume. Top: Bergamot, Black Currant and Orris. Heart: Jasmine, Caramel and Lily of the Valley. Base: Vanilla, Musk and Patchouli."
    },
    {
        "slug": "hot_mess_woman_edp_100ml",
        "name": "Bella Vita Hot Mess! Woman Luxury Eau De Parfum (100ml)",
        "price": 899, "mrp": 899, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Daring and vibrant party perfume. Top: Citrus Mandarin. Heart: Passionfruit. Base: Sensual Musk."
    },
    # 08 - 11: Classic Unisex/100ml (Page 6)
    {
        "slug": "white_oud_edp_100ml",
        "name": "Bella Vita White Oud Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Sophisticated woody oriental fragrance. Top: Artemisia, Lemon and Orange. Heart: Freesia, Blackcurrant and Patchouli. Base: Tobacco, Amber and Musk."
    },
    {
        "slug": "skai_aquatic_edc_100ml",
        "name": "Bella Vita Skai Aquatic Eau De Cologne (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Cologne",
        "description": "Refreshing breezy aquatic fragrance. Top: Bergamot, Coriander, Mandarin and Pineapple. Heart: Clary Sage, Lavender, Leather and Pink Pepper. Base: Patchouli."
    },
    {
        "slug": "fresh_unisex_edt_100ml",
        "name": "Bella Vita Fresh Unisex Eau De Toilette (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Toilette",
        "description": "Crisp revitalizing everyday fragrance. Top: Sweet Almond, Bergamot, Fresh Green. Heart: Lavender, Orange Blossom, Orris. Base: Ylang-Ylang."
    },
    {
        "slug": "honey_oud_edp_100ml",
        "name": "Bella Vita Honey Oud Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Sweet nectar and warm oud blend. Top: Honey, Bergamot. Heart: Oud, Rose, Patchouli. Base: Oud, Amber, Vanilla, Musk."
    },
    # 12 - 15: Man/Unisex 100ml (Page 7)
    {
        "slug": "night_fever_edp_100ml",
        "name": "Bella Vita Night Fever Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Intoxicating nightlife fragrance. Top: Spices and Fresh Citrus. Heart: Aromatic Woods. Base: Amber and Musk."
    },
    {
        "slug": "beast_edp_100ml",
        "name": "Bella Vita Beast Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Bold charismatic scent. Top: Raspberry, Birch, Benzoin, Geranium. Heart: Cypriol, Leather, Patchouli, Saffron. Base: Ambergris, Balsamic, Oud, Vanilla, Rose."
    },
    {
        "slug": "pure_musk_edp_100ml",
        "name": "Bella Vita Pure Musk Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Clean velvety comfort. Top: Aldehydes and Lily of the Valley. Heart: Sandalwood and Powdery Accord. Base: Tolu Balsam, Tonka Bean, Vanilla."
    },
    {
        "slug": "dynamite_edp_100ml",
        "name": "Bella Vita Dynamite Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Energetic aromatic explosion. Top: Lemon, Mandarin, Cardamom, Pear, Melon, Bergamot. Heart: Galbanum, Jasmine, Cedarwood. Base: Musk, Amber, Caramel, Marine."
    },
    # 16 - 18: Woman 100ml (Page 8)
    {
        "slug": "glam_woman_edp_100ml",
        "name": "Bella Vita Glam Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Chic Parisian floral elegance. Top: African Orange. Heart: Jasmine. Base: White Honey, Patchouli, Rose, Virginia Cedar."
    },
    {
        "slug": "date_woman_edp_100ml",
        "name": "Bella Vita Date Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Romantic sensual evening perfume. Top: Pink Pepper and Red Fruits. Heart: Jasmine, Orange Blossom, Violet. Base: Moss, Musk, Powdery Vanilla."
    },
    {
        "slug": "rose_woman_edp_100ml",
        "name": "Bella Vita Rose Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Romantic blooming velvety rose. Top: Candied Rose Petals. Heart: Peony and Turkish Rose. Base: Cashmere Musk and Amber."
    },
    # 19 - 21: Woman 100ml (Page 9)
    {
        "slug": "blush_woman_edp_100ml",
        "name": "Bella Vita Blush Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Sweet playful floral fragrance. Top: Tropical Red Fruits. Heart: Musk, Vanilla, Violet. Base: Sandalwood, Cedarwood, Moss."
    },
    {
        "slug": "senorita_woman_edp_100ml",
        "name": "Bella Vita Senorita Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Fruity oriental party fragrance. Top: Yuzu, Pomegranate, Mint. Heart: Peony, Lotus, Magnolia. Base: Musk, Mahogany, Amber."
    },
    {
        "slug": "bellavita_woman_kiss_edp_100ml",
        "name": "Bella Vita Kiss Woman Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Alluring fruity floral blend. Top: Red Berries and Mandarin. Heart: Violet and Orchid. Base: Sweet Amber and Musk."
    },
    # 22 - 25: Man 100ml (Page 10)
    {
        "slug": "ceo_man_edp_100ml",
        "name": "Bella Vita CEO Man Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Iconic boardroom signature scent. Top: Lemon and Sugar. Heart: Lavender. Base: Vetiver, Moss and Tonka."
    },
    {
        "slug": "klub_man_edp_100ml",
        "name": "Bella Vita Klub Man Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Energetic party lifestyle fragrance. Top: Lemon, Pineapple, Blackcurrant, Apple. Heart: Birch, Jasmine, Rose. Base: Musk, Amber, Vanilla, Patchouli."
    },
    {
        "slug": "goat_man_edp_100ml",
        "name": "Bella Vita G.O.A.T. Man Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Greatest Of All Time masculine scent. Top: Bergamot, Lavender, Pepper. Heart: Patchouli, Iris. Base: Vetiver, Cedarwood, Leather."
    },
    {
        "slug": "impact_man_edc_100ml",
        "name": "Bella Vita Impact Man Eau De Cologne (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Cologne",
        "description": "Bold dynamic freshness. Top: Green Citrus and Mandarin. Heart: Nutmeg and Cardamom. Base: Sandalwood and Amber."
    },
    # 26 - 28: Man 100ml (Page 11)
    {
        "slug": "you_man_edp_100ml",
        "name": "Bella Vita You Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Confident magnetic individual scent. Top: Bergamot. Heart: Lavender. Base: Tonka Bean."
    },
    {
        "slug": "supercharge_man_edp_100ml",
        "name": "Bella Vita Supercharge Man Eau De Parfum (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "High-octane sport adrenaline boost. Top: Grapefruit, Sea Notes. Heart: Bay Leaf, Jasmine. Base: Guaiac Wood, Oakmoss, Ambergris."
    },
    {
        "slug": "oud_parfum_100ml",
        "name": "Bella Vita Oud Parfum Luxury Fragrance (100ml)",
        "price": 599, "mrp": 599, "capacity": "100ml", "sub_category": "Eau De Parfum",
        "description": "Intense traditional eastern oud essence. Top: Saffron and Incense. Heart: Smoky Rose and Amber. Base: Pure Agarwood."
    },
    # 29 - 31: Mood Collection for Him 50ml (Page 12)
    {
        "slug": "magnetic_for_him_edp_50ml",
        "name": "Bella Vita Magnetic for Him Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Charismatic evening mood fragrance. Top: Grapefruit, Cardamom, Mint. Heart: Cinnamon, Clove, Geranium, Jasmine. Base: Cedarwood, Musk, Vetiver, Vanilla."
    },
    {
        "slug": "alpha_for_him_edp_50ml",
        "name": "Bella Vita Alpha for Him Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Leader dominant signature mood. Top: Bergamot, Lemon, Mandarin, Cardamom, Tea. Heart: Lily Of The Valley, Jasmine, Orange Blossom, Pepper. Base: Cedarwood, Tabac, Musk."
    },
    {
        "slug": "fantasy_for_him_edp_50ml",
        "name": "Bella Vita Fantasy for Him Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Mystical playful mood fragrance. Top: Exotic Spices. Heart: Cedar and Amber. Base: Warm Tonka and Vanilla."
    },
    # 32 - 34: Mood Collection for Her 50ml (Page 13)
    {
        "slug": "magnetic_for_her_edp_50ml",
        "name": "Bella Vita Magnetic for Her Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Hypnotic feminine allure. Top: Cassis, Almond, Cherry, Lychee. Heart: Rose, Peony, Jasmine, Ylang-Ylang. Base: Caramel, Tonka Bean, Vanilla, Ambrostar."
    },
    {
        "slug": "alpha_for_her_edp_50ml",
        "name": "Bella Vita Alpha for Her Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Empowered boss woman signature. Top: Mandarin, Orange, Bergamot, Orange Blossom. Heart: Jasmine, Lavender, Rose, Violet, Vetiver. Base: Patchouli, Musk, Bourbon Vanilla."
    },
    {
        "slug": "fantasy_for_her_edp_50ml",
        "name": "Bella Vita Fantasy for Her Eau De Parfum (50ml)",
        "price": 549, "mrp": 549, "capacity": "50ml", "sub_category": "Mood Collection",
        "description": "Dreamy fairy-tale floral mood. Top: Saffron, Orange, Pink Pepper, Cassis. Heart: Jasmine, Rose, Cinnamon Bark, Magnolia. Base: Moss, Musk, Patchouli, Cedarwood."
    },
    # 35 - 37: Gourmet Collection 100ml (Page 14)
    {
        "slug": "mango_gourmet_edp_100ml",
        "name": "Bella Vita Mango Gourmet Eau De Parfum (100ml)",
        "price": 649, "mrp": 649, "capacity": "100ml", "sub_category": "Gourmet Collection",
        "description": "Delectable juicy tropical confection. Top: Mango, Orris, Orange Blossom. Heart: Ylang, Amber, Coconut. Base: Siam Benzoin, Vanilla, Sandalwood."
    },
    {
        "slug": "pistachio_gourmet_edp_100ml",
        "name": "Bella Vita Pistachio Gourmet Eau De Parfum (100ml)",
        "price": 649, "mrp": 649, "capacity": "100ml", "sub_category": "Gourmet Collection",
        "description": "Creamy nutty decadent pastry aroma. Top: Nutty Pistachio and Rum. Heart: Jasmine, Lily of the Valley, Pear, Peach. Base: Cotton Candy, Vanilla, Marshmallow, Cedar."
    },
    {
        "slug": "vanilla_gourmet_edp_100ml",
        "name": "Bella Vita Vanilla Gourmet Eau De Parfum (100ml)",
        "price": 649, "mrp": 649, "capacity": "100ml", "sub_category": "Gourmet Collection",
        "description": "Warm velvety sweet bakery comfort. Top: Aldehydes, Heliotrope, Coconut, Vanilla. Heart: Vanilla and Mango. Base: White Musk, Coconut, Vanilla Absolute."
    },
    # 38 - 40: Luxury Gift Sets (Page 15)
    {
        "slug": "luxury_oud_experience_set_4x20ml",
        "name": "Bella Vita Luxury Oud Experience Gift Set (4 x 20ml)",
        "price": 899, "mrp": 899, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Royal artisanal gift set featuring 4 iconic oud perfumes: Oud Dark, Oud Parfum, White Oud, Oud Gold (20ml each)."
    },
    {
        "slug": "luxury_collection_gift_set_4x20ml",
        "name": "Bella Vita Luxury Collection Gift Set (4 x 20ml)",
        "price": 999, "mrp": 999, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Ultra luxury gift box containing 4 bestselling perfumes: CEO Man Intense, B.L.U. Man, Ocean Man, Oud Gold (20ml each)."
    },
    {
        "slug": "hot_and_classy_gift_set_2x50ml",
        "name": "Bella Vita Hot & Classy Women Gift Set (2 x 50ml)",
        "price": 999, "mrp": 999, "capacity": "2 x 50ml", "sub_category": "Gift Set",
        "description": "Fabulous women's luxury duo gift pack featuring Hot Mess! Woman & D.I.V.A. Woman (50ml each)."
    },
    # 41 - 43: Mood Sets & Beast Mode (Page 16)
    {
        "slug": "mood_collection_gift_set_him_3x15ml",
        "name": "Bella Vita Mood Collection Gift Set for Him (3 x 15ml)",
        "price": 649, "mrp": 649, "capacity": "3 x 15ml", "sub_category": "Gift Set",
        "description": "3 pocket mood perfumes for men: Alpha for Him, Fantasy for Him, Magnetic for Him (15ml each)."
    },
    {
        "slug": "mood_collection_gift_set_her_3x15ml",
        "name": "Bella Vita Mood Collection Gift Set for Her (3 x 15ml)",
        "price": 649, "mrp": 649, "capacity": "3 x 15ml", "sub_category": "Gift Set",
        "description": "3 pocket mood perfumes for women: Alpha for Her, Fantasy for Her, Magnetic for Her (15ml each)."
    },
    {
        "slug": "beast_mode_gift_set_man_4x20ml",
        "name": "Bella Vita Beast Mode Gift Set for Man (4 x 20ml)",
        "price": 699, "mrp": 699, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Raw masculine confidence kit: Elixir No.1, You, Amour, Vibes (20ml each)."
    },
    # 44 - 46: Luxury Perfume Gift Sets 4x20ml (Page 17)
    {
        "slug": "luxury_gift_set_man_4x20ml",
        "name": "Bella Vita Luxury Perfume Gift Set for Man (4 x 20ml)",
        "price": 649, "mrp": 649, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Best gift set for men featuring G.O.A.T. Man, Oud Parfum, CEO Man, Klub Man (20ml each)."
    },
    {
        "slug": "luxury_gift_set_woman_4x20ml",
        "name": "Bella Vita Luxury Perfume Gift Set for Woman (4 x 20ml)",
        "price": 649, "mrp": 649, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Gorgeous gift box for women: Rose Woman, Glam Woman, Date Woman, Senorita Woman (20ml each)."
    },
    {
        "slug": "luxury_unisex_gift_set_4x20ml",
        "name": "Bella Vita Luxury Unisex Gift Set (4 x 20ml)",
        "price": 649, "mrp": 649, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Versatile all-gender gift pack: Fresh Unisex, Skai Aquatic, Honey Oud, White Oud (20ml each)."
    },
    # 47 - 48: Unisex Gift Sets (Page 18)
    {
        "slug": "unisex_scents_gift_set_4x20ml",
        "name": "Bella Vita Unisex Scents Gift Set (4 x 20ml)",
        "price": 599, "mrp": 599, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Exotic evening unisex assortment: Night Fever, Devil, Narco, Pure Musk (20ml each)."
    },
    {
        "slug": "gourmet_collection_gift_set_3x20ml",
        "name": "Bella Vita Gourmet Collection Gift Set (3 x 20ml)",
        "price": 599, "mrp": 599, "capacity": "3 x 20ml", "sub_category": "Gift Set",
        "description": "Dessert-inspired mini fragrance set: Mango, Pistachio, Vanilla (20ml each)."
    },
    # 49 - 50: All Star & Be Iconic Sets (Page 19)
    {
        "slug": "all_star_gift_set_man_4x20ml",
        "name": "Bella Vita All Star Gift Set for Man (4 x 20ml)",
        "price": 649, "mrp": 649, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Stellar masculine discovery pack: Legend, Swagger, Alpha, Vibes (20ml each)."
    },
    {
        "slug": "be_iconic_gift_set_woman_4x20ml",
        "name": "Bella Vita Be Iconic Gift Set for Woman (4 x 20ml)",
        "price": 649, "mrp": 649, "capacity": "4 x 20ml", "sub_category": "Gift Set",
        "description": "Iconic women's fragrance discovery set: Charm, Expose, Blush, Diva (20ml each)."
    },
    # 51 - 54: Mini Luxury Perfumes 20ml (Page 20)
    {
        "slug": "white_oud_pocket_perfume_20ml",
        "name": "Bella Vita White Oud Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Travel-friendly White Oud spray. Top: Artemisia, Lemon. Heart: Freesia, Blackcurrant. Base: Tobacco, Amber."
    },
    {
        "slug": "skai_aquatic_pocket_perfume_20ml",
        "name": "Bella Vita Skai Aquatic Pocket Cologne (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Pocket size breezy freshness. Top: Bergamot, Mandarin. Heart: Lavender, Leather. Base: Patchouli."
    },
    {
        "slug": "ceo_man_pocket_perfume_20ml",
        "name": "Bella Vita CEO Man Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Executive presence everywhere you go. Top: Lemon. Heart: Lavender. Base: Vetiver, Tonka."
    },
    {
        "slug": "honey_oud_pocket_perfume_20ml",
        "name": "Bella Vita Honey Oud Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Pocket-sized sweet oud elixir. Top: Honey, Bergamot. Heart: Rose, Patchouli. Base: Oud, Vanilla, Amber."
    },
    # 55 - 58: Mini Perfumes 20ml (Page 21)
    {
        "slug": "glam_woman_pocket_perfume_20ml",
        "name": "Bella Vita Glam Woman Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Chic floral pocket spray. Top: African Orange. Heart: Jasmine. Base: White Honey, Patchouli, Rose."
    },
    {
        "slug": "date_woman_pocket_perfume_20ml",
        "name": "Bella Vita Date Woman Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Sensual travel spray for romantic evenings. Top: Pink Pepper. Heart: Jasmine, Violet. Base: Musk, Vanilla."
    },
    {
        "slug": "senorita_woman_pocket_perfume_20ml",
        "name": "Bella Vita Senorita Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Fruity oriental pocket spray. Top: Yuzu, Pomegranate. Heart: Peony, Lotus. Base: Mahogany, Amber."
    },
    {
        "slug": "rose_woman_pocket_perfume_20ml",
        "name": "Bella Vita Rose Woman Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Pocket spray blooming rose water and amber musk."
    },
    # 59 - 62: Mini & Combos 20ml (Page 22)
    {
        "slug": "fresh_unisex_pocket_perfume_20ml",
        "name": "Bella Vita Fresh Unisex Pocket Perfume (20ml)",
        "price": 175, "mrp": 175, "capacity": "20ml", "sub_category": "Pocket Perfume",
        "description": "Crisp green pocket splash. Top: Sweet Almond. Heart: Orange Blossom. Base: Ylang-Ylang."
    },
    {
        "slug": "combo_ceo_man_white_oud_2x20ml",
        "name": "Bella Vita Duo Combo: CEO Man + White Oud (2 x 20ml)",
        "price": 349, "mrp": 349, "capacity": "2 x 20ml", "sub_category": "Combo Pack",
        "description": "Powerful 2-piece combo pairing CEO Man and White Oud (20ml each)."
    },
    {
        "slug": "combo_honey_oud_white_oud_2x20ml",
        "name": "Bella Vita Duo Combo: Honey Oud + White Oud (2 x 20ml)",
        "price": 349, "mrp": 349, "capacity": "2 x 20ml", "sub_category": "Combo Pack",
        "description": "Artisanal oud lovers pair: Honey Oud and White Oud (20ml each)."
    },
    {
        "slug": "combo_skai_aquatic_fresh_2x20ml",
        "name": "Bella Vita Duo Combo: Skai Aquatic + Fresh Unisex (2 x 20ml)",
        "price": 349, "mrp": 349, "capacity": "2 x 20ml", "sub_category": "Combo Pack",
        "description": "Ultra fresh breezy dual pack: Skai Aquatic and Fresh Unisex (20ml each)."
    },
    # 63 - 65: No Gas Deos 150ml (Page 23)
    {
        "slug": "ceo_man_deo_parfum_150ml",
        "name": "Bella Vita CEO Man No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Zero gas long-lasting deodorant spray. Top: Ylang-Ylang, Pink Pepper, Bergamot. Heart: Plum, Lily of the Valley. Base: Tonka, Vanilla, Vetiver."
    },
    {
        "slug": "white_oud_deo_parfum_150ml",
        "name": "Bella Vita White Oud No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Long-lasting zero gas luxury deo spray. Top: Artemisia Lemon. Heart: Freesia, Blackcurrant. Base: Tobacco, Amber."
    },
    {
        "slug": "skai_aquatic_deo_parfum_150ml",
        "name": "Bella Vita Skai Aquatic No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Marine freshness zero gas body spray. Top: Bergamot, Pineapple. Heart: Clary Sage, Lavender. Base: Patchouli."
    },
    # 66 - 69: No Gas Deos 150ml (Page 24)
    {
        "slug": "klub_man_deo_parfum_150ml",
        "name": "Bella Vita Klub Man No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Zero gas party body spray. Top: Lemon, Apple. Heart: Birch, Jasmine. Base: Vanilla, Patchouli."
    },
    {
        "slug": "honey_oud_deo_parfum_150ml",
        "name": "Bella Vita Honey Oud No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Sweet oriental zero gas body spray. Top: Honey, Bergamot. Heart: Rose, Patchouli. Base: Vanilla, Oud."
    },
    {
        "slug": "date_woman_deo_parfum_150ml",
        "name": "Bella Vita Date Woman No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Enchanting romantic zero gas deodorant spray. Top: Pink Pepper, Red Fruits. Heart: Jasmine, Violet. Base: Vanilla, Musk."
    },
    {
        "slug": "glam_woman_deo_parfum_150ml",
        "name": "Bella Vita Glam Woman No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Parisian chic zero gas body spray. Top: African Orange. Heart: Jasmine. Base: White Honey, Patchouli."
    },
    # 70 - 73: No Gas Deos 150ml (Page 25)
    {
        "slug": "blush_deo_parfum_150ml",
        "name": "Bella Vita Blush No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Fruity floral zero gas deodorant. Top: Tropical Red Fruits. Heart: Musk, Vanilla. Base: Sandalwood, Cedarwood."
    },
    {
        "slug": "fresh_unisex_deo_parfum_150ml",
        "name": "Bella Vita Fresh Unisex No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Everyday revitalizing zero gas deo spray. Top: Almond, Green. Heart: Lavender, Orris. Base: Ylang-Ylang."
    },
    {
        "slug": "you_deo_parfum_150ml",
        "name": "Bella Vita You No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Dynamic daily zero gas deodorant. Top: Bergamot. Heart: Lavender. Base: Tonka Bean."
    },
    {
        "slug": "pure_musk_deo_parfum_150ml",
        "name": "Bella Vita Pure Musk No Gas Deo Parfum (150ml)",
        "price": 249, "mrp": 249, "capacity": "150ml", "sub_category": "Deo Parfum",
        "description": "Velvety sensual zero gas deodorant. Top: Aldehydes, Lily of the Valley. Heart: Sandalwood. Base: Tonka, Vanilla."
    },
    # 74 - 75: Perfumed Bathing Bars (Page 26)
    {
        "slug": "perfumed_bathing_bar_women_pack_3",
        "name": "Bella Vita Perfumed Bathing Bar for Women (Pack of 3)",
        "price": 199, "mrp": 199, "capacity": "Pack of 3", "sub_category": "Bath & Body",
        "description": "Luxury moisturising soap trio: Date Woman, Glam Woman, and White Oud Bathing Bars."
    },
    {
        "slug": "perfumed_bathing_bar_men_pack_3",
        "name": "Bella Vita Perfumed Bathing Bar for Men (Pack of 3)",
        "price": 199, "mrp": 199, "capacity": "Pack of 3", "sub_category": "Bath & Body",
        "description": "Invigorating executive soap trio: CEO Man, Skai Aquatic, and White Oud Bathing Bars."
    },
    # 76 - 78: Body Mists 150ml (Page 27)
    {
        "slug": "date_woman_body_mist_150ml",
        "name": "Bella Vita Date Woman Luxury Body Mist (150ml)",
        "price": 349, "mrp": 349, "capacity": "150ml", "sub_category": "Body Mist",
        "description": "All-over fragrant body mist spray. Top: Pink Pepper, Red Fruits. Heart: Jasmine, Violet. Base: Powdery Vanilla, Musk."
    },
    {
        "slug": "glam_woman_body_mist_150ml",
        "name": "Bella Vita Glam Woman Luxury Body Mist (150ml)",
        "price": 349, "mrp": 349, "capacity": "150ml", "sub_category": "Body Mist",
        "description": "Delicate all-day body fragrance spray. Top: African Orange. Heart: Jasmine. Base: White Honey, Patchouli."
    },
    {
        "slug": "senorita_woman_body_mist_150ml",
        "name": "Bella Vita Senorita Woman Luxury Body Mist (150ml)",
        "price": 349, "mrp": 349, "capacity": "150ml", "sub_category": "Body Mist",
        "description": "Fruity floral refreshing body mist. Top: Yuzu, Pomegranate, Mint. Heart: Peony, Lotus. Base: Amber, Mahogany."
    },
    # 79 - 82: Shower Gels 250ml (Page 28)
    {
        "slug": "skai_aquatic_shower_gel_250ml",
        "name": "Bella Vita Skai Aquatic Shower Gel (250ml)",
        "price": 199, "mrp": 199, "capacity": "250ml", "sub_category": "Bath & Body",
        "description": "Deep cleansing refreshing shower wash. Bergamot, Lavender, Patchouli notes."
    },
    {
        "slug": "ceo_man_shower_gel_250ml",
        "name": "Bella Vita CEO Man Luxury Shower Gel (250ml)",
        "price": 199, "mrp": 199, "capacity": "250ml", "sub_category": "Bath & Body",
        "description": "Energizing foaming body wash. Lemon, Lavender, Vetiver notes."
    },
    {
        "slug": "white_oud_shower_gel_250ml",
        "name": "Bella Vita White Oud Luxury Shower Gel (250ml)",
        "price": 199, "mrp": 199, "capacity": "250ml", "sub_category": "Bath & Body",
        "description": "Opulent woody oriental foaming body wash. Artemisia, Amber, Musk notes."
    },
    {
        "slug": "date_woman_shower_gel_250ml",
        "name": "Bella Vita Date Woman Luxury Shower Gel (250ml)",
        "price": 199, "mrp": 199, "capacity": "250ml", "sub_category": "Bath & Body",
        "description": "Hydrating romantic fragrant shower wash. Pink Pepper, Jasmine, Vanilla notes."
    },
    # 83 - 86: Shower Gels 500ml & Glam 250ml (Page 29)
    {
        "slug": "skai_aquatic_shower_gel_500ml",
        "name": "Bella Vita Skai Aquatic Jumbo Shower Gel (500ml)",
        "price": 299, "mrp": 299, "capacity": "500ml", "sub_category": "Bath & Body",
        "description": "Jumbo size refreshing aquatic foaming body wash. Bergamot, Mandarin, Patchouli."
    },
    {
        "slug": "ceo_man_shower_gel_500ml",
        "name": "Bella Vita CEO Man Jumbo Shower Gel (500ml)",
        "price": 299, "mrp": 299, "capacity": "500ml", "sub_category": "Bath & Body",
        "description": "Jumbo size invigorating executive body wash. Lemon, Lavender, Vetiver."
    },
    {
        "slug": "white_oud_shower_gel_500ml",
        "name": "Bella Vita White Oud Jumbo Shower Gel (500ml)",
        "price": 299, "mrp": 299, "capacity": "500ml", "sub_category": "Bath & Body",
        "description": "Jumbo size luxury oriental foaming body wash with rich amber oud aroma."
    },
    {
        "slug": "glam_woman_shower_gel_250ml",
        "name": "Bella Vita Glam Woman Luxury Shower Gel (250ml)",
        "price": 199, "mrp": 199, "capacity": "250ml", "sub_category": "Bath & Body",
        "description": "Silk smooth perfumed foaming shower gel. African Orange, Jasmine, White Honey."
    },
    # 87 - 89: Skincare & Face Washes (Page 30)
    {
        "slug": "hydrating_sunscreen_spf50_50ml",
        "name": "Bella Vita Hydrating Sunscreen SPF 50 PA++++ (50ml)",
        "price": 299, "mrp": 299, "capacity": "50ml", "sub_category": "Skincare",
        "description": "Broad spectrum UVA/UVB protection with lightweight quick-absorbing herbal hydration."
    },
    {
        "slug": "niacinamide_face_wash_110ml",
        "name": "Bella Vita Niacinamide Clarifying Face Wash (100ml + 10ml)",
        "price": 199, "mrp": 199, "capacity": "110ml", "sub_category": "Skincare",
        "description": "Skin clearing and blemish control cleanser. Fresh powdery aquatic scent."
    },
    {
        "slug": "salicylic_acid_face_wash_110ml",
        "name": "Bella Vita Salicylic Acid Anti-Acne Face Wash (100ml + 10ml)",
        "price": 199, "mrp": 199, "capacity": "110ml", "sub_category": "Skincare",
        "description": "Deep pore unclogging anti-acne face wash with gentle floral touch."
    },
    # 90 - 91: Face Washes (Page 31)
    {
        "slug": "neem_purifying_face_wash_110ml",
        "name": "Bella Vita Pure Neem Purifying Face Wash (100ml + 10ml)",
        "price": 199, "mrp": 199, "capacity": "110ml", "sub_category": "Skincare",
        "description": "Antiseptic herbal neem cleanser for refreshed, germ-free clear skin."
    },
    {
        "slug": "c_glow_brightening_face_wash_110ml",
        "name": "Bella Vita C-Glow Brightening Face Wash (100ml + 10ml)",
        "price": 199, "mrp": 199, "capacity": "110ml", "sub_category": "Skincare",
        "description": "Vitamin C antioxidant face wash for illuminated radiant glowing complexion."
    },
    # 92 - 95: Body Lotions 200ml (Page 32)
    {
        "slug": "aloe_vera_deep_hydration_body_lotion_200ml",
        "name": "Bella Vita Aloe Vera Deep Hydration Body Lotion (200ml)",
        "price": 299, "mrp": 299, "capacity": "200ml", "sub_category": "Body Lotion",
        "description": "Soothing daily body lotion with pure organic aloe vera extract. Fast-absorbing revitalizing moisture."
    },
    {
        "slug": "niacinamide_nourishing_body_lotion_200ml",
        "name": "Bella Vita Niacinamide Nourishing Body Lotion (200ml)",
        "price": 299, "mrp": 299, "capacity": "200ml", "sub_category": "Body Lotion",
        "description": "Even tone and skin barrier strengthening body lotion with active Niacinamide."
    },
    {
        "slug": "kumkumadi_ayurvedic_body_lotion_200ml",
        "name": "Bella Vita Kumkumadi Ayurvedic Radiance Body Lotion (200ml)",
        "price": 299, "mrp": 299, "capacity": "200ml", "sub_category": "Body Lotion",
        "description": "Traditional Ayurvedic saffron glow lotion for deeply hydrated luminous skin."
    },
    {
        "slug": "vitamin_c_brightening_body_lotion_200ml",
        "name": "Bella Vita Vitamin C Brightening Body Lotion (200ml)",
        "price": 299, "mrp": 299, "capacity": "200ml", "sub_category": "Body Lotion",
        "description": "Radiance boosting antioxidant body lotion enriched with Vitamin C for bright, smooth skin."
    }
]

def main():
    print("=" * 60)
    print("🚀 BELLA VITA CATALOG INGESTION ENGINE")
    print("=" * 60)

    # 1. Gather screenshots
    sc_files = sorted([f for f in os.listdir(SCREENSHOTS_DIR) if f.startswith("Screenshot 2026-10-05 at 7.")])
    print(f"Found {len(sc_files)} product screenshots.")
    print(f"Target products defined: {len(PRODUCTS)}")
    assert len(sc_files) == len(PRODUCTS), f"Mismatch: {len(sc_files)} screenshots vs {len(PRODUCTS)} products!"

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)

    catalog_entries = []

    # 2. Process images & convert to WebP
    print("\n📸 Converting Screenshots to Optimized WebP Assets...")
    for idx, (p, sc_file) in enumerate(zip(PRODUCTS, sc_files)):
        src_path = os.path.join(SCREENSHOTS_DIR, sc_file)
        webp_name = f"bellavita_{p['slug']}.webp"
        webp_path = os.path.join(OUTPUT_IMG_DIR, webp_name)
        web_url = f"/images/products/{webp_name}"

        # Pillow WebP optimization
        im = Image.open(src_path).convert("RGB")
        # Resize to max 600x600 if larger while maintaining aspect ratio
        im.thumbnail((600, 600), Image.Resampling.LANCZOS)
        im.save(webp_path, "WEBP", quality=85, method=6)
        file_size = os.path.getsize(webp_path) / 1024

        prod_id = f"bellavita_{p['slug']}"
        entry = {
            "id": prod_id,
            "name": p["name"],
            "brand": "Bella Vita Luxury",
            "category_id": "fashion",
            "sub_category": p.get("sub_category", "Fragrance"),
            "tags": f"fashion, lifestyle, fragrance, perfume, luxury, gifts, bellavita, {p['slug'].replace('_', ' ')}",
            "description": p["description"],
            "price": p["price"],
            "mrp": p["mrp"],
            "capacity": p.get("capacity", ""),
            "image_url": web_url,
            "badge": "LUXURY",
            "is_active": True,
            "stock": 50,
            "has_variants": False
        }
        catalog_entries.append(entry)

        if idx % 10 == 0 or idx == len(PRODUCTS) - 1:
            print(f"  [{idx+1:02d}/{len(PRODUCTS)}] Saved {webp_name} ({file_size:.1f} KB)")

    print(f"✓ All {len(catalog_entries)} images optimized & saved to public/images/products/")

    # 3. Update Master Catalog JSONs
    print("\n📦 Updating Master Catalog JSON files...")
    for cat_path in MASTER_CATALOG_PATHS:
        existing = []
        if os.path.exists(cat_path):
            with open(cat_path, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception:
                    existing = []

        # Remove any existing bellavita entries to prevent duplication
        filtered = [x for x in existing if not str(x.get("id", "")).startswith("bellavita_")]
        merged = filtered + catalog_entries

        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {cat_path}: Updated total products to {len(merged)} (added {len(catalog_entries)} Bella Vita entries)")

    # 4. Synchronize with Supabase Cloud DB
    print("\n☁️ Synchronizing with Supabase Cloud Database...")
    ctx = ssl._create_unverified_context()
    
    # Check if fashion category exists in Supabase
    cat_req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/categories?id=eq.fashion",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
    )
    with urllib.request.urlopen(cat_req, context=ctx) as r:
        cat_data = json.loads(r.read().decode("utf-8"))
        if not cat_data:
            print("  Creating 'fashion' category in Supabase...")
            create_cat_req = urllib.request.Request(
                f"{SUPABASE_URL}/rest/v1/categories",
                data=json.dumps([{
                    "id": "fashion",
                    "name": "Fashion",
                    "display_order": 7,
                    "is_active": True
                }]).encode("utf-8"),
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                method="POST"
            )
            try:
                urllib.request.urlopen(create_cat_req, context=ctx)
                print("  ✓ 'fashion' category created.")
            except Exception as e:
                print("  Category insert note:", e)

    # Insert/Upsert products in Supabase
    db_rows = []
    for c in catalog_entries:
        db_rows.append({
            "id": c["id"],
            "shop_id": SHOP_ID,
            "name": c["name"],
            "description": c["description"],
            "price": c["price"],
            "category_id": "fashion",
            "image_url": c["image_url"],
            "stock": c["stock"],
            "is_active": True
        })

    # Batch upsert in chunks of 50
    batch_size = 50
    for i in range(0, len(db_rows), batch_size):
        chunk = db_rows[i:i + batch_size]
        upsert_req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/products?on_conflict=shop_id,id",
            data=json.dumps(chunk).encode("utf-8"),
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(upsert_req, context=ctx) as r:
                print(f"  ✓ Upserted Supabase batch {i//batch_size + 1} ({len(chunk)} items)")
        except urllib.error.HTTPError as e:
            print(f"  Error upserting batch: {e.code} - {e.read().decode('utf-8')}")

    print("\n🎉 Bella Vita catalog successfully ingested into Fashion category!")
    print(f"Total products now in catalog: {len(merged)}")

if __name__ == "__main__":
    main()
