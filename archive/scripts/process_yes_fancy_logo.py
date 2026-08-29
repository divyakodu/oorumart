#!/usr/bin/env python3
"""
scripts/process_yes_fancy_logo.py

1. Takes AI-generated logo image.
2. Removes background to create a true transparent PNG logo.
3. Generates a luxury animated GIF with a golden shining light sweep effect.
4. Saves assets to /public/images/ and artifacts folder.
"""

import os
import glob
from PIL import Image, ImageEnhance, ImageOps

AI_IMAGE_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_brand_logo_1787760936003.jpg"
PUBLIC_PNG_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_transparent.png"
PUBLIC_GIF_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_animated.gif"
ARTIFACT_GIF_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_logo_animated.gif"

def process_logo():
    print("🚀 Processing AI Logo & Creating Transparent PNG + Gold Shining GIF...\n")

    img = Image.open(AI_IMAGE_PATH).convert("RGBA")
    width, height = img.size

    # 1. Convert checkerboard / grey background to transparent
    # The gold text/crown has distinct luminance & saturation compared to dark grey checkerboard
    datas = img.getdata()
    new_data = []

    for item in datas:
        r, g, b, a = item
        # Check if pixel is grey background (R, G, B are close and relatively dark/medium)
        diff_rg = abs(r - g)
        diff_gb = abs(g - b)
        avg_rgb = (r + g + b) / 3.0

        # Gold text pixels have higher R than B (warm golden tint)
        is_gold = (r > b + 20) or (r > 160 and g > 130 and b < 140)

        if not is_gold and diff_rg < 15 and diff_gb < 15:
            # Transparent background
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))

    transparent_img = Image.new("RGBA", img.size)
    transparent_img.putdata(new_data)

    # Crop to content box
    bbox = transparent_img.getbbox()
    if bbox:
        transparent_img = transparent_img.crop(bbox)

    # Add 20px padding around cropped logo
    padded_width = transparent_img.width + 40
    padded_height = transparent_img.height + 40
    final_png = Image.new("RGBA", (padded_width, padded_height), (0, 0, 0, 0))
    final_png.paste(transparent_img, (20, 20))

    final_png.save(PUBLIC_PNG_PATH, "PNG")
    print(f"  ✅ Transparent PNG saved to '{PUBLIC_PNG_PATH}' ({final_png.width}x{final_png.height})")

    # 2. Create Gold Shining Light Sweep Animated GIF
    frames = []
    num_frames = 20

    for i in range(num_frames):
        frame = final_png.copy()
        shine_mask = Image.new("L", frame.size, 0)

        # Calculate diagonal light sweep position across image
        sweep_x = int((i / float(num_frames)) * (frame.width + frame.height + 100)) - 50

        # Draw a diagonal shining light beam across mask
        for y in range(frame.height):
            for x in range(frame.width):
                pos = x + y
                dist = abs(pos - sweep_x)
                if dist < 45:
                    # Light brightness gradient inside shine beam
                    brightness = int(255 * (1.0 - (dist / 45.0)))
                    shine_mask.putpixel((x, y), brightness)

        # Apply golden bright shine overlay
        enhancer = ImageEnhance.Brightness(frame)
        bright_frame = enhancer.enhance(1.4)

        # Composite light shine frame
        composited = Image.composite(bright_frame, frame, shine_mask)
        frames.append(composited)

    # Save as animated GIF with 60ms frame delay (smooth 16fps animation)
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

    print(f"  ✨ Animated Gold Shining GIF saved to '{PUBLIC_GIF_PATH}' and artifact folder!")

if __name__ == '__main__':
    process_logo()
