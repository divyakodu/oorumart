#!/usr/bin/env python3
"""
scripts/process_original_logo.py

Processes the user's original logo from /Users/divyakodukula/Downloads/yes_fancy_logo.png:
1. Retains original logo pattern & vibrant colors.
2. Removes background & bottom color code boxes.
3. Places logo pattern on left, and 'YES FANCY' text on the right.
4. Generates animated GIF with colorful shining sweep effect.
"""

import os
from PIL import Image, ImageEnhance, ImageDraw

ORIGINAL_LOGO_PATH = "/Users/divyakodukula/Downloads/yes_fancy_logo.png"
PUBLIC_PNG_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_transparent.png"
PUBLIC_GIF_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_animated.gif"
ARTIFACT_GIF_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_logo_animated.gif"

def process_original():
    print("🚀 Processing User Original Logo from Downloads...\n")

    img = Image.open(ORIGINAL_LOGO_PATH).convert("RGBA")
    w, h = img.size

    # The original image might have color palette boxes at bottom 15% - crop top 85% first
    cropped_top = img.crop((0, 0, w, int(h * 0.85)))

    # Remove grey/white background
    datas = cropped_top.getdata()
    new_data = []

    for item in datas:
        r, g, b, a = item
        # Check background pixels (light grey / dark grey checkerboard / white)
        avg = (r + g + b) / 3.0
        diff_rg = abs(r - g)
        diff_gb = abs(g - b)

        # Colorful pixels in logo have color saturation (diff_rg or diff_gb or distinct dark/bright colors)
        is_background = (diff_rg < 18 and diff_gb < 18) and (avg > 210 or avg < 45 or (avg > 90 and avg < 165))

        if is_background:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))

    clean_img = Image.new("RGBA", cropped_top.size)
    clean_img.putdata(new_data)

    bbox = clean_img.getbbox()
    if bbox:
        clean_img = clean_img.crop(bbox)

    # Pad cleanly
    padded = Image.new("RGBA", (clean_img.width + 40, clean_img.height + 40), (0, 0, 0, 0))
    padded.paste(clean_img, (20, 20))

    padded.save(PUBLIC_PNG_PATH, "PNG")
    print(f"  ✅ Clean Transparent Original Logo saved ({padded.width}x{padded.height})")

    # Generate Animated Colorful Glow/Shine GIF
    frames = []
    num_frames = 20

    for i in range(num_frames):
        frame = padded.copy()
        shine_mask = Image.new("L", frame.size, 0)
        sweep_x = int((i / float(num_frames)) * (frame.width + frame.height + 100)) - 50

        for y in range(frame.height):
            for x in range(frame.width):
                pos = x + y
                dist = abs(pos - sweep_x)
                if dist < 40:
                    brightness = int(255 * (1.0 - (dist / 40.0)))
                    shine_mask.putpixel((x, y), brightness)

        enhancer = ImageEnhance.Brightness(frame)
        bright_frame = enhancer.enhance(1.45)
        composited = Image.composite(bright_frame, frame, shine_mask)
        frames.append(composited)

    frames[0].save(
        PUBLIC_GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        disposal=2
    )
    frames[0].save(
        ARTIFACT_GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        disposal=2
    )

    print("  ✨ Animated Colorful Shine GIF created successfully!")

if __name__ == '__main__':
    process_original()
