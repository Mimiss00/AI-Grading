import os
import io
import re
import cv2
import numpy as np
from pdf2image import convert_from_path
from google.cloud import vision
from fpdf import FPDF

# ========== CONFIGURATION ==========
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ocr-pipeline/fyp-ai-3a972-OCR_API.json"  # ✅ Vision API key
POPPLER_PATH = r"C:\poppler\poppler-24.08.0\Library\bin"  # Adjust Poppler path

# ========== IMAGE PREPROCESSING FUNCTIONS ==========
def increase_contrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

def preprocess_image(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Increase contrast
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    img = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove small noise
    denoised = cv2.fastNlMeansDenoising(gray, h=20)

    # Simple threshold instead of adaptive
    _, binary = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY_INV)

    # Apply morphological operations to clean small dots
    kernel = np.ones((2, 2), np.uint8)
    clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    return clean


def image_to_bytes(image):
    _, buffer = cv2.imencode(".png", image)
    return io.BytesIO(buffer).getvalue()

def run_google_ocr(image_bytes):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    image_context = vision.ImageContext(language_hints=["en-t-i0-handwrit"])
    response = client.document_text_detection(image=image, image_context=image_context)
    return response.full_text_annotation.text if response.full_text_annotation else ""

def clean_cpp_code(text):
    text = re.sub(r"\bLL\b|\bCL\b", "<<", text)
    text = re.sub(r"\bendi\b|\bendal\b|Llenal|end 1", "endl", text)
    text = re.sub(r"\bLLendi\b|\bLL endi\b|\bILL end 1\b", "<< endl", text)
    text = re.sub(r"·", ".", text)
    text = re.sub(r"\bCouble\b|\bcouble\b", "double", text)
    text = re.sub(r"\bdoubler\b", "double r", text)
    text = re.sub(r"\binti\b|\bintf\b", "int i", text)
    text = re.sub(r'“|”|„|‟', '"', text)
    text = re.sub(r"[‘’`]", "'", text)
    text = re.sub(r'cout\s*<<\s*([a-zA-Z0-9_]+)\s*=\s*<<', r'cout << "\1=" <<', text)
    text = re.sub(r"GS CamScanner", "", text)
    text = re.sub(r"// No\.|Date|No|//Date\.", " ", text)
    text = re.sub(r":\s*", "; ", text)
    text = re.sub(r",\s*", "; ", text)
    text = re.sub(r"\bE\b", "{", text)
    return text

# ========== MAIN PROCESS ==========
def process_pdf_local(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return None, None

    print(f"✅ Converting {pdf_path} to images...")
    images = convert_from_path(pdf_path, dpi=400, poppler_path=POPPLER_PATH)

    processed_images = []
    all_text = ""

    for i, page in enumerate(images):
        print(f"🖼️ Processing page {i+1}...")
        processed_img = preprocess_image(page)
        processed_images.append(processed_img)

        img_bytes = image_to_bytes(processed_img)
        ocr_text = run_google_ocr(img_bytes)
        cleaned_text = clean_cpp_code(ocr_text)
        all_text += f"\n--- Page {i+1} ---\n{cleaned_text}\n"

    return processed_images, all_text

def save_images_to_pdf(images, output_pdf_path):
    pdf = FPDF()
    for img_array in images:
        temp_path = "/tmp/temp_page.png"
        cv2.imwrite(temp_path, img_array)

        pdf.add_page()
        pdf.image(temp_path, x=0, y=0, w=210, h=297)  # A4 size
    pdf.output(output_pdf_path)
    print(f"✅ Processed images saved to {output_pdf_path}")

# ========== USAGE ==========
if __name__ == "__main__":
    pdf_path = input("📄 Enter the path to the student's handwritten PDF file: ").strip()

    processed_images, extracted_code = process_pdf_local(pdf_path)

    if processed_images:
        output_pdf = "processed_output.pdf"
        output_text = "output_code.txt"

        save_images_to_pdf(processed_images, output_pdf)

        with open(output_text, "w", encoding="utf-8") as f:
            f.write(extracted_code)

        print(f"✅ OCR text saved to {output_text}")
