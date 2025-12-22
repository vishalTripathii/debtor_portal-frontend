import fitz
import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pathlib import Path
from pyzbar.pyzbar import decode
import re

INPUT_FOLDER = "files"
OUTPUT_FOLDER = "qr_output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


def extract_ref1(img):
    """Extracts Ref1 number from OCR text"""
    text = pytesseract.image_to_string(img, lang="eng+tha")
    print("\n===== OCR TEXT FROM REF SECTION =====")
    print(text)

    match = re.search(r"Ref1[^\d]*(\d{6,20})", text)  # precise detection
    if match:
        print(f"✔ Ref1 extracted: {match.group(1)}")
        return match.group(1)

    print("✗ Ref1 not found")
    return None


def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    print(f"\n============================================")
    print(f"PROCESSING FILE: {pdf_path.name}")
    print("============================================")

    for page_no in range(len(doc)):
        page = doc[page_no]
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        h, w = img.size[1], img.size[0]

        # ================= REF + QR CROP AREA =================
        ref_crop = img.crop((0, int(h * 0.12), w, int(h * 0.45)))
        qr_crop = img.crop((0, int(h * 0.45), int(w * 0.50), h))  # bottom-left area

        ref_crop.save("ref1_debug.jpg")
        qr_crop.save("qr_debug.jpg")
        print("Debug images saved: ref1_debug.jpg, qr_debug.jpg")

        # ================= Extract Ref1 =================
        ref1_value = extract_ref1(ref_crop)

        # ================= Detect QR =================
        opencv_img = cv2.cvtColor(np.array(qr_crop), cv2.COLOR_RGB2BGR)
        qr_codes = decode(opencv_img)

        if not qr_codes:
            print("✗ No QR detected in customer section")
            continue

        qr = qr_codes[0]  # first QR
        x, y, wbox, hbox = qr.rect
        qr_img = opencv_img[y:y+hbox, x:x+wbox]

        # ================= Save QR with correct filename =================
        if ref1_value:
            filename = f"{ref1_value}.jpg"
        else:
            filename = f"unknown_{page_no+1}.jpg"

        output_file = os.path.join(OUTPUT_FOLDER, filename)
        cv2.imwrite(output_file, qr_img)

        print(f"✔ QR extracted and saved -> {output_file}")

    doc.close()


if __name__ == "__main__":
    pdf_files = list(Path(INPUT_FOLDER).glob("*.pdf"))
    print(f"Found {len(pdf_files)} files in folder '{INPUT_FOLDER}'")

    for pdf in pdf_files:
        process_pdf(pdf)