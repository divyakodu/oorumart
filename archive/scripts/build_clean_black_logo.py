#!/usr/bin/env python3
"""
scripts/build_clean_black_logo.py

1. Crops ONLY the crown/symbol mark from /Users/divyakodukula/Downloads/yes_fancy_logo.png (stripping old text below crown).
2. Cleans background for ultra-high-resolution, vector-crisp rendering without embossing/pixelation.
3. Renders clean, sharp, solid black typography 'YES FANCY' to the right (like CHUMBAK in reference).
4. Saves transparent PNG & subtle animated GIF.
"""

import os
from PIL import Image, ImageEnhance, ImageFont, ImageDraw

ORIGINAL_LOGO_PATH = "/Users/divyakodukula/Downloads/yes_fancy_logo.png"
PUBLIC_PNG_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_transparent.png"
PUBLIC_GIF_PATH = "/Users/divyakodukula/Documents/oorumart/public/images/yes_fancy_logo_animated.gif"
ARTIFACT_GIF_PATH = "/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02/yes_fancy_logo_animated.gif"

def build_clean_logo():
    print("🚀 Building Vector-Crisp Logo (Crown Icon Left + Sharp Black Text Right)...\n")

    img = Image.open(ORIGINAL_LOGO_PATH).convert("RGBA")
    w, h = img.size

    # 1. Crop ONLY the crown mark at top (top 42% of image, excluding text below crown)
    crown_crop = img.crop((0, 0, w, int(h * 0.42)))

    # Remove background pixels
    datas = crown_crop.getdata()
    new_data = []

    for item in datas:
        r, g, b, a = item
        avg = (r + g + b) / 3.0
        diff_rg = abs(r - g)
        diff_gb = abs(g - b)

        # Background condition (grey/white background or checkerboard)
        is_background = (diff_rg < 18 and diff_gb < 18) and (avg > 200 or avg < 40 or (avg > 90 and avg < 165))

        if is_background:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))

    clean_crown = Image.new("RGBA", crown_crop.size)
    clean_crown.putdata(new_data)

    bbox = clean_crown.getbbox()
    if bbox:
        clean_crown = clean_crown.crop(bbox)

    # Resize crown icon to clean crisp height e.g. 56px
    target_height = 56
    aspect = clean_crown.width / float(clean_crown.height)
    target_width = int(target_height * aspect)
    crown_resized = clean_crown.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # 2. Build Horizontal Canvas for Crown (Left) + Crisp Black Text (Right)
    canvas_w = target_width + 260
    canvas_h = 64
    logo_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Paste Crown on Left
    crown_y = int((canvas_h - target_height) / 2.0)
    logo_canvas.paste(crown_resized, (0, crown_y))

    # 3. Draw Clean, Solid Black Typography 'YES FANCY' on Right
    draw = ImageDraw.Draw(logo_canvas)

    font = None
    possible_fonts = [
        "/System/Library/Fonts/Supplemental/PlayfairDisplay-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Montserrat-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
    ]
    for fpath in possible_fonts:
        if os.path.exists(fpath):
            try:
                font = ImageFont.truetype(fpath, 34)
                break
            except Exception:
                pass

    if font is None:
        font = ImageFont.load_default()

    text_x = target_width + 18
    text_y = int((canvas_h - 34) / 2.0) - 3

    # Solid, crisp black text (#0F172A) with zero embossing or shadows
    draw.text((text_x, text_y), "YES FANCY", font=font, fill=(15, 23, 42, 255))

    # Save transparent PNG
    logo_canvas.save(PUBLIC_PNG_PATH, "PNG")
    print(f"  ✅ Crisp Transparent PNG saved to '{PUBLIC_PNG_PATH}' ({canvas_w}x{canvas_h})")

    # 4. Generate Subtle Animated Shine Sweep GIF
    frames = []
    num_frames = 20

    for i in range(num_frames):
        frame = logo_canvas.copy()
        shine_mask = Image.new("L", frame.size, 0)
        sweep_x = int((i / float(num_frames)) * (frame.width + frame.height + 80)) - 40

        for y in range(frame.height):
            for x in range(frame.width):
                pos = x + y
                dist = abs(pos - sweep_x)
                if dist < 35:
                    brightness = int(220 * (1.0 - (dist / 35.0)))
                    shine_mask.putpixel((x, y), brightness)

        enhancer = ImageEnhance.Brightness(frame)
        bright_frame = enhancer.enhance(1.3)
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

    print(f"  ✨ Subtle Animated Shine GIF saved to '{PUBLIC_GIF_PATH}' and artifact folder!")

if __name__ == '__main__':
    build_clean_logo()
