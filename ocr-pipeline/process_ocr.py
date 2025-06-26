import os
import io
import json
import re
import cv2
import numpy as np
from pdf2image import convert_from_path
from google.cloud import vision
import firebase_admin
from firebase_admin import credentials, storage, firestore
import urllib.parse
import json
import base64
import tempfile

# ========== CONFIGURATION ==========
# ========== POPPLER PATH (Adjust based on environment) ==========
if os.name == 'nt':
    # Windows (local)
    POPPLER_PATH = r"C:\poppler\poppler-24.08.0\Library\bin"
else:
    # Linux (e.g. Railway)
    POPPLER_PATH = "/usr/bin"

# ========== GOOGLE VISION SETUP ==========
vision_base64 = os.getenv("GOOGLE_VISION_JSON_BASE64")
if not vision_base64:
    raise ValueError("Missing GOOGLE_VISION_JSON_BASE64 environment variable")

vision_json = base64.b64decode(vision_base64)

with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_cred:
    temp_cred.write(vision_json.decode())
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred.name  # Required by Google Vision API

vision_client = vision.ImageAnnotatorClient()

# ========== FIREBASE ADMIN SETUP ==========
firebase_base64 = os.getenv("GOOGLE_CREDS_JSON_BASE64")
if not firebase_base64:
    raise ValueError("Missing GOOGLE_CREDS_JSON_BASE64 environment variable")

firebase_json = base64.b64decode(firebase_base64)
firebase_dict = json.loads(firebase_json)
cred = credentials.Certificate(firebase_dict)

FIREBASE_BUCKET_NAME = "fyp-ai-3a972.firebasestorage.app"

firebase_admin.initialize_app(cred, {
    'storageBucket': FIREBASE_BUCKET_NAME
})

bucket = storage.bucket()

# ========== IMAGE PREPROCESSING ==========
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
    image = vision.Image(content=image_bytes)
    image_context = vision.ImageContext(language_hints=["en-t-i0-handwrit"])
    response = vision_client.document_text_detection(image=image, image_context=image_context)
    return response.full_text_annotation.text if response.full_text_annotation else ""

# ========== C++ TEXT CLEANUP ==========
def clean_cpp_code(text):
    text = re.sub(r"\bLL\b|\bCL\b", "<<", text)
    text = re.sub(r"\bendi\b|\bendal\b|Llenal|end 1", "endl", text)
    text = re.sub(r"\bLLendi\b", "<< endl", text)
    text = re.sub(r"\bILL end 1\b", "<< endl", text)
    text = re.sub(r"·", ".", text)
    text = re.sub(r"\bCouble\b|\bcouble\b", "double", text)
    text = re.sub(r"\bdoubler\b", "double r", text)
    text = re.sub(r"\binti\b|\bintf\b", "int i", text)
    text = re.sub(r"Int\((.)\)", r"int(\1)", text)
    text = re.sub(r"\bi = Int\(s\);", "i = int(s);", text)
    text = re.sub(r'“|”|„|‟', '"', text)
    text = re.sub(r"[‘’`]", "'", text)
    text = re.sub(r'cout\s*<<\s*([a-zA-Z0-9_]+)\s*=\s*<<', r'cout << "\1=" <<', text)
    text = re.sub(r"GS CamScanner", "", text)
    text = re.sub(r"// No\.", " ", text)
    text = re.sub(r"Date", " ", text)
    text = re.sub(r"No", " ", text)
    text = re.sub(r":\s*", "; ", text)
    text = re.sub(r",\s*", "; ", text)
    text = re.sub(r"\bE\b", "{", text)
    return text

# ========== MAIN PROCESS ==========
def main():
    db = firestore.client()

    # 🔥 Get latest submission
    submissions_ref = db.collection('submissions')
    submissions = submissions_ref.order_by('submittedAt', direction=firestore.Query.DESCENDING).limit(1)
    submissions = list(submissions.stream())

    if not submissions:
        print("❌ No submissions found!")
        return

    submission = submissions[0].to_dict()
    firebase_pdf_url = submission['fileURL']

    # 🔥 Extract and decode path
    try:
        parsed_path = firebase_pdf_url.split('/o/')[1].split('?')[0]
        storage_path = urllib.parse.unquote(parsed_path)
    except Exception as e:
        print(f"❌ Error parsing path from URL: {e}")
        return

    print("🛠 Storage Path:", storage_path)

    original_filename = os.path.basename(storage_path)
    local_pdf_path = original_filename

    # 🔥 Download PDF
    try:
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)
        blob.download_to_filename(local_pdf_path)
        print(f"✅ Downloaded: {storage_path} → {local_pdf_path}")
    except Exception as e:
        print(f"❌ Firebase Storage error: {e}")
        return

    # 🔥 Convert PDF to images
    images = convert_from_path(local_pdf_path, dpi=400, poppler_path=POPPLER_PATH)
    all_text = ""

    for i, page in enumerate(images):
        print(f"📄 Processing page {i + 1}/{len(images)}...")
        processed_img = preprocess_image(page)
        img_bytes = image_to_bytes(processed_img)
        ocr_text = run_google_ocr(img_bytes)
        cleaned_result = clean_cpp_code(ocr_text)
        all_text += f"\n--- Page {i + 1} ---\n{cleaned_result.strip()}\n"

    # 🔥 Save output JSON
    output_json = {
        "fileName": os.path.basename(local_pdf_path),
        "assignmentType": "C++",
        "pages": len(images),
        "rawText": all_text
    }


    os.makedirs("extracted_answers", exist_ok=True)  # 🛠️ Create folder if not exists

    output_path = os.path.join("extracted_answers", os.path.basename(local_pdf_path).replace('.pdf', '.json'))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4)

    print(f"✅ OCR completed. Cleaned text saved to '{output_path}'.")


    print("✅ OCR completed and saved to extracted_answers.json")

# ========== RUN ==========
if __name__ == "__main__":
    main()
