import fitz  # PyMuPDF
import io
import os
from PIL import Image, ImageChops

def extract_and_format_catalog_images(pdf_path, output_dir="extracted_images"):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    # Product naming sequence matching page order in the PDF
    image_names = [
        "milton_insignia_casserole.png",
        "milton_valenza_casserole.png",
        "milton_oyster_casserole.png",
        "milton_pearl_casserole.png",
        "milton_venice_casserole.png",
        "milton_curve_casserole.png",
        "milton_royal_casserole.png",
        "milton_marvel_casserole.png",
        "milton_orchid_casserole.png",
        "milton_flora_casserole.png",
        "milton_buffet_casserole.png",
        "milton_luxuria_casserole.png",
        "milton_tulip_casserole.png",
        "milton_sphere_casserole.png",
        "milton_galaxia_casserole.png"
    ]

    extracted_count = 0
    for page_idx, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Load into Pillow
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            # Filter out tiny icon artifacts (like small logos or vector bullets)
            if img.width < 100 or img.height < 100:
                continue

            # Crop excess whitespace around the product
            bg = Image.new(img.mode, img.size, (255, 255, 255, 0))
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()
            if bbox:
                img = img.crop(bbox)

            # Pad into a square 1:1 canvas with transparent/clean background
            max_side = max(img.width, img.height)
            square_img = Image.new("RGBA", (max_side, max_side), (255, 255, 255, 0))
            offset = ((max_side - img.width) // 2, (max_side - img.height) // 2)
            square_img.paste(img, offset)

            # Assign matching name from list
            out_name = (
                image_names[extracted_count] 
                if extracted_count < len(image_names) 
                else f"casserole_extracted_{extracted_count}.png"
            )
            out_path = os.path.join(output_dir, out_name)
            square_img.save(out_path, format="PNG")
            print(f"Saved: {out_path} ({square_img.size})")

            extracted_count += 1

    print(f"\nDone! Extracted and formatted {extracted_count} images into '{output_dir}'.")

if __name__ == "__main__":
    extract_and_format_catalog_images("CasseroleSeries - low - Mobile 2.pdf")
