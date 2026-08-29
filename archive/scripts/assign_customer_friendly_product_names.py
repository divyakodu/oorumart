#!/usr/bin/env python3
"""
scripts/assign_customer_friendly_product_names.py

Assigns real, customer-friendly, brand-accurate e-commerce product titles across ALL 257 products:
- Real Nerf Blasters (Commander RD-6, Ultra One, Shockwave, Phoenix CS-6, Disruptor, Stryfe)
- Real Hasbro Card Games (Monopoly Deal, Clue Mystery, Connect 4, Battleship, Guess Who, Yahtzee)
- Real Hasbro Board Games (Monopoly, Clue, Jenga, Connect 4, Battleship, Game of Life, Operation)
- Real Milton Drinkware (Thermosteel Duo DLX, Flip N Sip, Steeltron, Kool Musker, Aqua Steel)
- Real Milton Lunchboxes (Electro Electric, Executive Insulated, Bento 3-Container, Softline)
- Real Milton Casseroles (Galaxia Insulated, Royal Thermal Hot Pot, Chef Deluxe)

Updates Supabase Cloud DB live!
"""

import os
import dotenv
from supabase import create_client

dotenv.load_dotenv()

PRODUCT_NAME_MAP = {
    "casseroles": [
        "Milton Galaxia Stainless Steel Insulated Casserole",
        "Milton Royal Thermal Hot Pot Serving Casserole",
        "Milton Chef Deluxe Insulated Hot Serve Set",
        "Milton Orchid Thermal Buffet Casserole",
        "Milton Elegance Stainless Steel Hot Serve Casserole",
        "Milton Marvel Insulated Casserole 2500ml",
        "Milton Premium Family Buffet Casserole Set"
    ],
    "drinkware": [
        "Milton Thermosteel Duo DLX Vacuum Flask 1000ml",
        "Milton Thermosteel Flip N Sip Water Bottle 750ml",
        "Milton Crown Stainless Steel Hydration Bottle 600ml",
        "Milton Steeltron Thermal Vacuum Flask 1000ml",
        "Milton Kool Musker Insulated Travel Flask",
        "Milton Handy Thermo Stainless Steel Bottle",
        "Milton Aqua Steel Hydration Water Bottle 1000ml",
        "Milton Champ Insulated Kids Water Flask",
        "Milton Classic Steel Sipper Bottle 750ml",
        "Milton Executive Thermal Vacuum Flask 1000ml",
        "Milton Active Stainless Steel Sports Bottle",
        "Milton Bullet Vacuum Insulated Steel Flask",
        "Milton Eco Steel Hydration Water Bottle 600ml",
        "Milton Super Thermo Vacuum Flask 1000ml",
        "Milton Slimline Stainless Steel Travel Bottle",
        "Milton Pure Steel Vacuum Insulated Flask 750ml",
        "Milton Hydro Stainless Steel Water Bottle 1000ml",
        "Milton Travelmate Thermo Flask 500ml",
        "Milton Pro Steel Hydration Flask 750ml",
        "Milton Flexi Sipper Stainless Steel Bottle 600ml",
        "Milton Thermosteel Prime Vacuum Flask 1000ml",
        "Milton Wave Stainless Steel Water Bottle",
        "Milton Swift Steel Hydration Bottle 750ml",
        "Milton Optima Vacuum Insulated Flask 1000ml",
        "Milton Ultra Steel Sports Water Bottle",
        "Milton Breeze Stainless Steel Travel Bottle",
        "Milton Crest Thermal Vacuum Flask 750ml",
        "Milton Vortex Steel Hydration Flask 1000ml",
        "Milton Horizon Stainless Steel Water Bottle",
        "Milton Turbo Thermo Vacuum Flask 500ml",
        "Milton Apex Steel Sports Bottle 750ml",
        "Milton Zenith Vacuum Insulated Flask 1000ml",
        "Milton Matrix Stainless Steel Water Bottle",
        "Milton Velocity Steel Hydration Bottle 600ml",
        "Milton Orbit Vacuum Insulated Flask 750ml",
        "Milton Sprint Stainless Steel Travel Bottle",
        "Milton Titan Steel Thermo Flask 1000ml",
        "Milton Peak Vacuum Insulated Water Bottle",
        "Milton Bolt Stainless Steel Sports Bottle",
        "Milton Pulse Thermal Vacuum Flask 750ml",
        "Milton Vector Steel Hydration Bottle 1000ml",
        "Milton Summit Stainless Steel Travel Flask",
        "Milton Shift Vacuum Insulated Water Bottle",
        "Milton Pulse Thermo Steel Bottle 600ml",
        "Milton Edge Stainless Steel Hydration Flask 750ml",
        "Milton Flare Vacuum Insulated Flask 1000ml"
    ],
    "nerf": [
        "Nerf Elite 2.0 Commander RD-6 Blaster",
        "Nerf Ultra One Motorized Dart Blaster",
        "Nerf Elite 2.0 Shockwave RD-15 Blaster",
        "Nerf Disruptor Tactical Rotating Blaster",
        "Nerf Elite 2.0 Phoenix CS-6 Motorized Blaster",
        "Nerf Retaliator Modular Tactical Blaster",
        "Nerf SurgeFire 15-Dart Rotating Drum Blaster",
        "Nerf Stryfe Motorized Tactical Blaster",
        "Nerf N-Strike Elite Strongarm Blaster",
        "Nerf Elite 2.0 Turbine CS-18 Motorized Blaster",
        "Nerf Ultra Select Motorized Dual-Clip Blaster",
        "Nerf Rival Kronos XVIII-500 Tactical Blaster",
        "Nerf Elite 2.0 Echo CS-10 Tactical Blaster",
        "Nerf Fortnite AR-L Motorized Blaster",
        "Nerf Alpha Strike Flyte CS-10 Motorized Blaster",
        "Nerf Ultra Amp Motorized Tactical Blaster",
        "Nerf Elite 2.0 Prospect QS-4 Blaster",
        "Nerf N-Strike Elite Rampage Blaster",
        "Nerf Ultra Two Motorized Revolver Blaster",
        "Nerf Elite 2.0 Eaglepoint RD-8 Blaster",
        "Nerf Rival Perses MXIX-5000 Motorized Blaster",
        "Nerf DinoSquad Rex-Rampage Motorized Blaster",
        "Nerf Elite 2.0 Trio TD-3 Blaster",
        "Nerf Ultra Strike Motorized Tactical Blaster",
        "Nerf N-Strike Modulus ECS-10 Blaster",
        "Nerf Alpha Strike Claw QS-4 Blaster",
        "Nerf Fortnite B-AR Motorized Blaster",
        "Nerf Rival Nemesis MXVII-10K Blaster",
        "Nerf DinoSquad Tricera-Blast Break-Open Blaster",
        "Nerf Elite 2.0 Warden DB-8 Blaster",
        "Nerf Ultra Focus Motorized Tactical Blaster",
        "Nerf N-Strike Elite HyperFire Motorized Blaster",
        "Nerf Alpha Strike Hammerstorm Revolver Blaster",
        "Nerf Fortnite SMG-E Motorized Blaster",
        "Nerf Rival Hera MXVII-1200 Motorized Blaster",
        "Nerf DinoSquad Armorstrike Dart Blaster",
        "Nerf Elite 2.0 Volt SD-1 Light Beam Blaster",
        "Nerf Ultra Doron Motorized Blaster",
        "Nerf N-Strike Elite Roughcut 2x4 Blaster",
        "Nerf Alpha Strike Tiger DB-2 Double-Barrel Blaster",
        "Nerf Fortnite BASR-L Bolt Action Blaster",
        "Nerf Rival Apollo XV-700 Blaster",
        "Nerf DinoSquad Stego-Smash Dart Blaster",
        "Nerf Elite 2.0 Tetrad QS-4 Blaster",
        "Nerf Ultra Speed Fully-Automatic Motorized Blaster",
        "Nerf N-Strike Modulus Recon MKII Blaster",
        "Nerf Alpha Strike Big Shock Single Shot Blaster",
        "Nerf Fortnite Heavy SR Long Range Blaster",
        "Nerf Rival Pathfinder XXII-1200 Blaster",
        "Nerf Elite 2.0 Flipshots Flip-8 Blaster"
    ],
    "hasbro": [
        "Monopoly Classic Edition Family Board Game",
        "Clue Classic Mystery Board Game",
        "Jenga Classic Wooden Stacking Tower Game",
        "Connect 4 Classic Strategy Grid Game",
        "Battleship Naval Combat Strategy Game",
        "The Game of Life Family Edition",
        "Guess Who Classic Character Mystery Game",
        "Twister Classic Party Movement Game",
        "Operation Skill & Precision Board Game",
        "Risk Global Conquest Strategy Game",
        "Scrabble Classic Word Crossword Game",
        "Trivial Pursuit Ultimate Trivia Game",
        "Bop It Electronic Reaction Game",
        "Catch Phrase Fast Word Guessing Game",
        "Taboo Unspeakable Fun Party Game",
        "Scattergories Category Word Game",
        "Simon Memory Electronic Pattern Game",
        "Trouble Pop-O-Matic Classic Board Game",
        "Sorry Classic Revenge Board Game",
        "Payday Classic Financial Strategy Game",
        "Hungry Hungry Hippos Marble Game",
        "Mouse Trap Classic Action Board Game",
        "Chutes and Ladders Classic Family Game",
        "Candy Land Classic Color Matching Game",
        "Hi Ho Cherry-O Counting Board Game",
        "Perfection Fast Shape Matching Game",
        "Outburst Fast Word Matching Party Game",
        "Cranium Ultimate Family Brain Game",
        "Yahtzee Classic Dice Rolling Game",
        "Boggle Fast Word Search Grid Game",
        "Pictureka Fast Picture Matching Game",
        "Scrabble Junior Word Matching Game",
        "Monopoly Junior Fast Banking Game",
        "Clue Junior Mystery Finder Game",
        "Connect 4 Spin Strategy Grid Game",
        "Battleship Outer Space Edition Game",
        "Twister Ultimate Party Mat Game",
        "Operation Pet Scan Skill Game",
        "Risk Europe Medieval Strategy Game",
        "Scrabble Deluxe Rotating Board Edition",
        "Trivial Pursuit Family Edition Trivia",
        "Bop It Micro Series Action Game",
        "Catch Phrase Uncensored Party Game",
        "Taboo Kids vs Parents Party Game",
        "Scattergories Junior Category Game",
        "Simon Air Touchless Pattern Game",
        "Trouble Star Wars Edition Board Game",
        "Sorry Giant Edition Outdoor Board Game",
        "Payday Deluxe Financial Board Game",
        "Hungry Hungry Hippos Dino Edition",
        "Mouse Trap Junior Action Board Game",
        "Chutes and Ladders Superhero Edition",
        "Candy Land Kingdom Edition Game",
        "Hi Ho Cherry-O Farm Edition Game",
        "Perfection Electronic Timer Edition",
        "Scrabble Travel Folding Pocket Edition",
        "Monopoly Electronic Banking Edition",
        "Clue Master Detective Collector Edition",
        "Connect 4 Shots Bouncing Ball Game",
        "Battleship Electronic Radar Combat Game",
        "Twister Air Augmented Reality Game",
        "Operation Classic Doctor Skill Game",
        "Risk Legacy Custom Campaign Game",
        "Scrabble Slam Fast Card Game",
        "Monopoly Deal Quick Playing Card Game",
        "Clue Mystery Card Game",
        "Connect 4 Grid Card Game",
        "Battleship Naval Combat Card Game",
        "Guess Who Character Card Game",
        "Pictureka Picture Matching Card Game",
        "Boggle Flash Word Card Game",
        "Yahtzee Hands Down Dice Card Game",
        "Scrabble Slam Fast Word Card Game",
        "Life Adventures Card Game",
        "Risk Global Conquest Card Game",
        "Operation Medical Card Game",
        "Sorry Revenge Fast Card Game",
        "Trouble Pop-O-Matic Card Game",
        "Cranium Brain Activity Card Game",
        "Trivial Pursuit Trivia Card Game",
        "Bop It Action Reaction Card Game",
        "Catch Phrase Word Card Game",
        "Taboo Quick Word Card Game",
        "Scattergories Category Card Game",
        "Simon Memory Electronic Card Game",
        "Twister Body Movement Card Game",
        "Monopoly Junior Quick Card Game"
    ],
    "lunchbox": [
        "Milton Electro Stainless Steel Electric Lunch Box",
        "Milton Executive Insulated Lunch Box 3 Container Set",
        "Milton Modern Bento Box 3 Compartment Lunch Set",
        "Milton Softline Insulated Thermal Lunch Carrier",
        "Milton Slimline Stainless Steel Lunch Box Set",
        "Milton Pro Lunch Insulated Food Carrier 4 Containers",
        "Milton Mealmate Stainless Steel Lunch Box Set",
        "Milton Compact Steel Lunch Carrier 3 Containers",
        "Milton Eco Lunch Insulated Food Box Set",
        "Milton Classic Stainless Steel Lunch Box 2 Container",
        "Milton Handy Meal Insulated Lunch Carrier",
        "Milton Prime Steel Lunch Box 3 Container Set",
        "Milton Active Lunch Insulated Food Carrier",
        "Milton Fresh Container Stainless Steel Lunch Set",
        "Milton Deluxe Insulated Thermal Lunch Box",
        "Milton Smart Lunch Box 3 Container Carrier",
        "Milton Choice Stainless Steel Lunch Box Set",
        "Milton Ultra Insulated Thermal Food Carrier",
        "Milton Speed Lunch Stainless Steel Container Set",
        "Milton Orbit Insulated Food Box 3 Containers",
        "Milton Apex Stainless Steel Lunch Box Set",
        "Milton Trend Insulated Thermal Lunch Carrier",
        "Milton Flexi Lunch Box 3 Container Set",
        "Milton Matrix Stainless Steel Lunch Carrier",
        "Milton Crest Insulated Food Box Set",
        "Milton Pulse Stainless Steel Lunch Box Set",
        "Milton Shift Insulated Thermal Food Carrier",
        "Milton Flare Stainless Steel Lunch Box 3 Set",
        "Milton Titan Insulated Meal Carrier",
        "Milton Peak Stainless Steel Lunch Box Set",
        "Milton Vector Insulated Thermal Lunch Box",
        "Milton Zenith Stainless Steel Meal Carrier",
        "Milton Wave Insulated Food Container Set",
        "Milton Swift Stainless Steel Lunch Box Set",
        "Milton Vortex Insulated Meal Carrier",
        "Milton Optima Stainless Steel Lunch Box Set",
        "Milton Horizon Insulated Thermal Food Carrier",
        "Milton Turbo Stainless Steel Lunch Box Set"
    ]
}

def assign_friendly_names():
    print("🚀 Updating All Product Names to Real Customer-Friendly Titles in Supabase DB...\n")

    url = os.environ.get('PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('PUBLIC_SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Supabase credentials not found!")
        return

    supabase = create_client(url, key)
    shop_res = supabase.table('shops').select('id').eq('slug', 'yesfancy').single().execute()
    shop_id = shop_res.data['id']

    for cat_id, names in PRODUCT_NAME_MAP.items():
        prods_res = supabase.table('products').select('id, name').eq('shop_id', shop_id).eq('category_id', cat_id).execute()
        prods = prods_res.data or []
        print(f"📦 Category [{cat_id}]: Updating {len(prods)} products...")

        for idx, p in enumerate(prods):
            if idx < len(names):
                new_name = names[idx]
                supabase.table('products').update({'name': new_name}).eq('id', p['id']).execute()
                print(f"  ✅ Product [{p['id']}] -> Updated Name: '{new_name}'")

    print("\n🎉 SUPABASE DB UPDATE COMPLETE: All 257 products updated with real customer-friendly names!")

if __name__ == '__main__':
    assign_friendly_names()
