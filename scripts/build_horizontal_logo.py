#!/usr/bin/env python3
"""
scripts/build_horizontal_logo.py

Builds the exact horizontal logo requested by user:
1. Logo Icon / Symbol on the LEFT (from original /Users/divyakodukula/Downloads/yes_fancy_logo.png).
2. 'YES FANCY' typography directly to the RIGHT of the icon.
3. 100% Transparent PNG background (zero grey box, zero color palette text).
4. Generates animated gold/colorful shining light sweep GIF.
"""

import os
from PIL import Image, ImageEnhance, ImageFont, ImageDraw

ORIGINAL_LOGO_PATH = "/Users/divyakodukula/Downloads/yes_fancy_logo.png"
PUBLIC_PNG_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_transparent.png"
PUBLIC_GIF_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_animated.gif"
ARTIFACT_GIF_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_logo_animated.gif"

def build_horizontal_logo():
    print("🚀 Building Horizontal Logo Layout (Icon Left + 'YES FANCY' Right)...\n")

    img = Image.open(ORIGINAL_LOGO_PATH).convert("RGBA")
    w, h = img.size

    # Crop the logo icon (top 60% of original image)
    icon_crop = img.crop((0, 0, w, int(h * 0.65)))

    # Remove background pixels
    datas = icon_crop.getdata()
    new_data = []

    for item in datas:
        r, g, b, a = item
        avg = (r + g + b) / 3.0
        diff_rg = abs(r - g)
        diff_gb = abs(g - b)

        # Background condition (grey/white checkerboard or background)
        is_background = (diff_rg < 18 and diff_gb < 18) and (avg > 200 or avg < 40 or (avg > 90 and avg < 165))

        if is_background:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))

    clean_icon = Image.new("RGBA", icon_crop.size)
    clean_icon.putdata(new_data)

    bbox = clean_icon.getbbox()
    if bbox:
        clean_icon = clean_icon.crop(bbox)

    # Resize icon to clean height e.g. 80px
    target_height = 80
    aspect = clean_icon.width / float(clean_icon.height)
    target_width = int(target_height * aspect)
    icon_resized = clean_icon.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # Create horizontal canvas for Icon (Left) + Text (Right)
    canvas_w = target_width + 360
    canvas_h = target_height + 20
    horizontal_logo = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Paste Icon on Left
    horizontal_logo.paste(icon_resized, (10, 10))

    # Draw 'YES FANCY' text to the RIGHT of icon
    draw = ImageDraw.Draw(horizontal_logo)

    # Use a bold serif font
    font = None
    possible_fonts = [
        "/System/Library/Fonts/Supplemental/PlayfairDisplay-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Times.ttc"
    ]
    for fpath in possible_fonts:
        if os.path.exists(fpath):
            try:
                font = ImageFont.truetype(fpath, 42)
                break
            except Exception:
                pass

    if font is None:
        font = ImageFont.load_default()

    # Draw text in rich gold color with subtle drop shadow
    text_x = target_width + 30
    text_y = int((canvas_h - 42) / 2.0) - 2

    # Drop shadow
    draw.text((text_x + 2, text_y + 2), "YES FANCY", font=font, fill=(15, 23, 42, 180))
    # Main gold text
    draw.text((text_x, text_y), "YES FANCY", font=font, fill=(212, 175, 55, 255))

    # Save transparent PNG
    horizontal_logo.save(PUBLIC_PNG_PATH, "PNG")
    print(f"  ✅ Transparent Horizontal PNG saved to '{PUBLIC_PNG_PATH}' ({canvas_w}x{canvas_h})")

    # Generate Animated Colorful/Gold Shining Light Sweep GIF
    frames = []
    num_frames = 20

    for i in range(num_frames):
        frame = horizontal_logo.copy()
        shine_mask = Image.new("L", frame.size, 0)
        sweep_x = int((i / float(num_frames)) * (frame.width + frame.height + 100)) - 50

        for y in range(frame.height):
            for x in range(frame.width):
                pos = x + y
                dist = abs(pos - sweep_x)
                if dist < 45:
                    brightness = int(255 * (1.0 - (dist / 45.0)))
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

    print(f"  ✨ Animated Gold Shining GIF saved to '{PUBLIC_GIF_PATH}' and artifact folder!")

if __name__ == '__main__':
    build_horizontal_logo()
