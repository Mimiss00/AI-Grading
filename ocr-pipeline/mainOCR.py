import os
import cv2
import io
import numpy as np
from pdf2image import convert_from_path
from google.cloud import vision
import re

# ========== CONFIGURATION ==========
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fyp-ai-3a972-OCR_API.json"
poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"
pdf_path = r"C:\Users\Syamimi Suhaimi\Documents\VSCode\templates\C++ assignment\C++ Handwritten_5.pdf"

# ========== IMAGE PROCESSING ==========
def increase_contrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

def preprocess_image(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img = increase_contrast(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    blurred = cv2.GaussianBlur(denoised, (5, 5), 0)
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 10)
    return binary

def image_to_bytes(image):
    _, buffer = cv2.imencode(".png", image)
    return io.BytesIO(buffer).getvalue()

# ========== GOOGLE VISION OCR ==========
def run_google_ocr(image_bytes):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    image_context = vision.ImageContext(language_hints=["en-t-i0-handwrit"])
    response = client.document_text_detection(image=image, image_context=image_context)
    return response.full_text_annotation.text if response.full_text_annotation else ""

# ========== TEXT CLEANUP ==========
def clean_code(text):
    # Common symbol corrections
    text = re.sub(r"\bLL\b", "<<", text)
    text = re.sub(r"\bCL\b", "<<", text)
    text = re.sub(r"\bendi\b|\bendal\b|Llenal|end 1", "endl", text)
    text = re.sub(r"\bLLendi\b", "<< endl", text)
    text = re.sub(r"\bLL endi\b", "<< endl", text)
    text = re.sub(r"\bILL end 1\b", "<< endl", text)
    text = re.sub(r"Llenal", "<< endl", text)
    text = re.sub(r"·", ".", text)
    
    # Common word fixes
    text = re.sub(r"\bCouble\b|\bcouble\b", "double", text)
    text = re.sub(r"\bdoubler\b", "double r", text)
    text = re.sub(r"\binti\b|\bintf\b", "int i", text)
    text = re.sub(r"Int\((.)\)", r"int(\1)", text)
    text = re.sub(r"\bi = Int\(s\);", "i = int(s);", text)
    
    # Quotes cleanup
    text = re.sub(r'“|”|„|‟', '"', text)
    text = re.sub(r"[‘’`]", "'", text)
    # Fix missing quotes around 'i=' and similar patterns
    text = re.sub(r'cout\s*<<\s*([a-zA-Z0-9_]+)\s*=\s*<<', r'cout << "\1=" <<', text)

    
    # Remove CamScanner watermark and OCR noise
    text = re.sub(r"GS CamScanner", "", text)
    text = re.sub(r"// No\.", " ", text)
    text = re.sub(r"Date", " ", text)
    text = re.sub(r"No", " ", text)
    text = re.sub(r"//Date\.", " ", text)



    # Fix stray colons or commas near code
    text = re.sub(r":\s*", "; ", text)
    text = re.sub(r",\s*", "; ", text)
    text = re.sub(r"\bE\b", "{", text)

    return text


# ========== MAIN LOOP ==========
images = convert_from_path(pdf_path, dpi=400, poppler_path=poppler_path)
all_text = ""

for i, page in enumerate(images):
    print(f"📄 Processing page {i + 1}/{len(images)}...")
    processed = preprocess_image(page)

    # Display the processed image before OCR
    window_name = f"Processed Page {i + 1}"
    # Resize the image for display (e.g., 40% of original size)
    display_img = cv2.resize(processed, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)
    cv2.imshow(window_name, display_img)
    print("🔍 Press any key in the image window to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    img_bytes = image_to_bytes(processed)
    ocr_text = run_google_ocr(img_bytes)
    cleaned_result = clean_code(ocr_text)

    all_text += f"\n--- Page {i + 1} ---\n{cleaned_result.strip()}\n"


# ========== SAVE OUTPUT ==========
output_path = "google_ocr_output.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(all_text)

print(f"✅ OCR complete using Google Vision. Output saved to '{output_path}'")
