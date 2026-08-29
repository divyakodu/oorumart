#!/usr/bin/env python3
"""
scripts/process_ai_crown_icon.py

1. Takes Google Image AI generated crown icon.
2. Removes white background to create true transparent PNG.
3. Generates animated gold shining light sweep GIF.
4. Saves assets to /public/images/.
"""

import os
from PIL import Image, ImageEnhance

AI_ICON_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_crown_icon_1787762858416.jpg"
PUBLIC_PNG_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_icon_transparent.png"
PUBLIC_GIF_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_icon_animated.gif"
ARTIFACT_GIF_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_icon_animated.gif"

def process_crown():
    print("🚀 Processing AI Crown Icon Mark...\n")

    img = Image.open(AI_ICON_PATH).convert("RGBA")

    # Remove white background
    datas = img.getdata()
    new_data = []

    for item in datas:
        r, g, b, a = item
        # White background condition
        if r > 240 and g > 240 and b > 240:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))

    clean_icon = Image.new("RGBA", img.size)
    clean_icon.putdata(new_data)

    bbox = clean_icon.getbbox()
    if bbox:
        clean_icon = clean_icon.crop(bbox)

    # Add 15px padding
    padded = Image.new("RGBA", (clean_icon.width + 30, clean_icon.height + 30), (0, 0, 0, 0))
    padded.paste(clean_icon, (15, 15))

    padded.save(PUBLIC_PNG_PATH, "PNG")
    print(f"  ✅ Transparent AI Crown PNG saved to '{PUBLIC_PNG_PATH}' ({padded.width}x{padded.height})")

    # Generate Animated Gold Shine GIF
    frames = []
    num_frames = 20

    for i in range(num_frames):
        frame = padded.copy()
        shine_mask = Image.new("L", frame.size, 0)
        sweep_x = int((i / float(num_frames)) * (frame.width + frame.height + 60)) - 30

        for y in range(frame.height):
            for x in range(frame.width):
                pos = x + y
                dist = abs(pos - sweep_x)
                if dist < 40:
                    brightness = int(240 * (1.0 - (dist / 40.0)))
                    shine_mask.putpixel((x, y), brightness)

        enhancer = ImageEnhance.Brightness(frame)
        bright_frame = enhancer.enhance(1.4)
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

    print(f"  ✨ Animated Crown Icon GIF saved to '{PUBLIC_GIF_PATH}' and artifact folder!")

if __name__ == '__main__':
    process_crown()
