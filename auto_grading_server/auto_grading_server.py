import os
import io
import json
import re
import time
import urllib.parse
import requests
import openai
import firebase_admin
import pytz
from firebase_admin import credentials, firestore, storage
from google.cloud import vision
from PyPDF2 import PdfMerger
from fpdf import FPDF
from pdf2image import convert_from_path
import cv2
import numpy as np
import traceback  # ⬅️ Make sure this is at the top of your file
from openai import OpenAI  # ✅ Required for openai>=1.0.0
import base64
import tempfile
from dotenv import load_dotenv



load_dotenv()
# ========== CONFIGURATION ==========
# Set your API keys and JSON paths
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ==== Google Vision API Setup ====
vision_base64 = os.getenv("GOOGLE_VISION_JSON_BASE64")
if not vision_base64:
    raise ValueError("Missing GOOGLE_VISION_JSON_BASE64 environment variable")

vision_json = base64.b64decode(vision_base64)

# Write decoded JSON to a temp file and set the env path
with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_cred:
    temp_cred.write(vision_json.decode())
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred.name


# ==== Firebase Admin SDK Setup ====
firebase_creds = os.getenv("GOOGLE_CREDS_JSON_BASE64")
if not firebase_creds:
    raise ValueError("Missing GOOGLE_CREDS_JSON_BASE64 environment variable")

cred_dict = json.loads(base64.b64decode(firebase_creds))
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    'storageBucket': 'fyp-ai-3a972.firebasestorage.app'
})

db = firestore.client()
bucket = storage.bucket()

POPPLER_PATH = r"C:\poppler\poppler-24.08.0\Library\bin"  # Change to your Poppler path

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
    binary = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        15, 10
    )
    return binary

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
    # Fix known OCR mistakes
    text = re.sub(r"\bLL\b|\bCL\b", "<<", text)
    text = re.sub(r"\bendi\b|\bendal\b|Llenal|end 1", "endl", text)
    text = re.sub(r"\bLLendi\b", "<< endl", text)
    text = re.sub(r'\bE\b', '{', text)
    text = re.sub(r"\bILL end 1\b", "<< endl", text)
    text = re.sub(r"\bCouble\b|\bcouble\b", "double", text)
    text = re.sub(r"\bdoubler\b", "double r", text)
    text = re.sub(r"\binti\b|\bintf\b", "int i", text)
    text = re.sub(r"Int\((.)\)", r"int(\1)", text)
    text = re.sub(r"\bi = Int\(s\);", "i = int(s);", text)
    text = re.sub(r'“|”|„|‟', '"', text)
    text = re.sub(r"[‘’`]", "'", text)
    text = re.sub(r'cout\s*<\s*<', 'cout <<', text)  # Normalize cout
    text = re.sub(r'<<\s*endl', '<< endl', text)

    # Remove common OCR garbage
    text = re.sub(r"·", ".", text)
    text = re.sub(r"CS CamScanner", "", text)
    text = re.sub(r"// No\.", " ", text)
    text = re.sub(r"Date", " ", text)
    text = re.sub(r"No", " ", text)

    # Fix colon and comma issues
    text = re.sub(r":\s*", "; ", text)
    text = re.sub(r",\s*", "; ", text)
    text = re.sub(r';', ';\n', text)              # Line break after semicolons
    text = re.sub(r'\{', '{\n', text)             # After opening brace
    text = re.sub(r'\}', '}\n', text)             # After closing brace

 

    # Remove junk after quotes
    text = re.sub(r'"\s*[.,;]', '"', text)
    text = re.sub(r'\s+[.,;]', '', text)
    text = re.sub(r'"\s*\n\s*"', '', text)  # Remove stray quote-only lines


    # Force proper code layout
    text = text.replace('{', '\n{\n')
    text = text.replace('}', '\n}\n')
    text = text.replace(';', ';\n')  # each semicolon = new line
    text = re.sub(r'cout\s*<<\s*"\s*(.*?)\s*"\s*;', r'cout << "\1";', text)


    # Final cleanup
    text = re.sub(r';', ';\n', text)             # Split after semicolons
    text = re.sub(r'\{', '{\n', text)            # Split after opening brace
    text = re.sub(r'\}', '}\n', text)            # Split after closing brace
    text = re.sub(r'\n+', '\n', text)            # Collapse multiple newlines
    text = re.sub(r'[ \t]+', ' ', text)          # Normalize whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(lines)




# ========== GRADING ==========
def extract_total_marks(answer_scheme):
    mark_values = re.findall(r'(\d+(?:\.\d+)?)\s*marks?', answer_scheme, re.IGNORECASE)
    total = sum(float(m) for m in mark_values)
    return int(round(total)) if total else 10

def ask_openai_grading(answer_scheme, student_answer):
    client = OpenAI(api_key=openai_api_key)  # ✅ New initialization

    student_lines = student_answer.strip().split('\n')
    numbered_student_answer = "\n".join([f"{idx+1} | {line}" for idx, line in enumerate(student_lines)])
    total_marks = extract_total_marks(answer_scheme)

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a strict but fair C++ programming lecturer who grades student code submissions.\n"
                f"Marking Scheme (Total: {total_marks} marks):\n"
                "- Variable declaration: 1 mark\n"
                "- Prompt and input statement: 1 mark\n"
                "- Correct use of if-else or logical flow: 4 marks\n"
                "- Output/display statement(s): 2 marks\n"
                "- Overall structure and syntax: 2 marks\n\n"
                "Instructions:\n"
                "- Use the model answer (answer scheme) as the reference.\n"
                "- Do not assume the question — only follow the logic and structure shown in the model answer.\n"
                "- For each line of the student's code, provide feedback using this format:\n"
                "  Line N | code // Correct (X marks) OR // Incorrect - explanation (0 marks)\n"
                f"Finish with 'Overall Score: X/{total_marks}' and Final Feedback."
            )
        },
        {
            "role": "user",
            "content": (
                f"Model Answer:\n{answer_scheme.strip()}\n\n"
                f"Student Submission:\n{numbered_student_answer.strip()}\n\n"
                f"Grade this based on the model answer. Format as instructed. Do not assume task."
            )
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("[ERROR] OpenAI call failed:", e)
        return "[ERROR] Grading failed due to OpenAI API error."



def create_feedback_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# ========== MAIN PROCESS ==========
def process_submission(submission_doc):
    submission_id = submission_doc.id
    submission = submission_doc.to_dict()

    file_url = submission.get("fileURL")
    assignment_id = submission.get("assignmentId")
    if not file_url or not assignment_id:
        print(f"❌ Missing fileURL or assignmentId for {submission_id}.")
        return

    # Fetch Assignment (for answer scheme)
    assignment_doc = db.collection('assignments').document(assignment_id).get()
    if not assignment_doc.exists:
        print(f"❌ Assignment not found for {assignment_id}")
        return
    assignment = assignment_doc.to_dict()
    answer_scheme_url = assignment.get("answerSchemeFileURL")

    if not answer_scheme_url:
        print("❌ No answer scheme available.")
        return

    # Download student PDF
    parsed_path = file_url.split('/o/')[1].split('?')[0]
    storage_path = urllib.parse.unquote(parsed_path)
    file_name = os.path.basename(storage_path)
    local_student_pdf = f"/tmp/{submission_id}_{file_name}"

    blob = bucket.blob(storage_path)
    blob.download_to_filename(local_student_pdf)
    print(f"✅ Downloaded student PDF: {file_name}")

    # ==== OCR process (support PDF and image files) ====
    all_text = ""
    images = []

    if local_student_pdf.lower().endswith(".pdf"):
        try:
            images = convert_from_path(local_student_pdf, dpi=400, poppler_path=POPPLER_PATH)
        except Exception as e:
            print(f"❌ Failed to process PDF: {e}")
            return
    elif local_student_pdf.lower().endswith((".jpg", ".jpeg", ".png")):
        from PIL import Image
        try:
            img = Image.open(local_student_pdf)
            images = [img]
        except Exception as e:
            print(f"❌ Failed to open image: {e}")
            return
    else:
        print(f"❌ Unsupported file format: {local_student_pdf}")
        return

    # Process all images (1 or more pages)
    for i, page in enumerate(images):
        print(f"🖼️ Processing page {i+1}...")
        processed_img = preprocess_image(page)
        img_bytes = image_to_bytes(processed_img)
        ocr_text = run_google_ocr(img_bytes)
        cleaned = clean_cpp_code(ocr_text)
        all_text += f"\n--- Page {i+1} ---\n{cleaned}\n"


    # Download answer scheme
    parsed_ans = answer_scheme_url.split('/o/')[1].split('?')[0]
    ans_path = urllib.parse.unquote(parsed_ans)
    local_answer_json = "/tmp/answer_scheme.json"
    blob = bucket.blob(ans_path)
    blob.download_to_filename(local_answer_json)
    with open(local_answer_json, "r", encoding="utf-8") as f:
        answer_scheme = f.read()

    # Grading
    print("🧠 Grading with OpenAI...")
    grading_result = ask_openai_grading(answer_scheme, all_text)

     # Create feedback PDF with unique name
    feedback_pdf_path = f"/tmp/{submission_id}_feedback.pdf"
    if os.path.exists(feedback_pdf_path):
        os.remove(feedback_pdf_path)
    create_feedback_pdf(grading_result, feedback_pdf_path)


    # Merge PDFs
    final_pdf_path = f"/tmp/{submission_id}_grading_final.pdf"
    merger = PdfMerger()
    merger.append(local_student_pdf)
    merger.append(feedback_pdf_path)
    merger.write(final_pdf_path)
    merger.close()
    print("✅ Merged final grading PDF.")

     # Upload final PDF
    grading_blob = bucket.blob(f'grading_results/{submission_id}_grading_final.pdf')
    grading_blob.upload_from_filename(final_pdf_path)
    grading_blob.make_public()
    grading_pdf_url = grading_blob.public_url
    print(f"✅ Uploaded grading PDF: {grading_pdf_url}")

    # Extract score
    all_matches = re.findall(r"Overall Score:\s*(\d{1,3}\s*/\s*\d{1,3})", grading_result, re.IGNORECASE)
    extracted_mark = all_matches[-1].replace(" ", "") if all_matches else "-"

    # Update Firestore
    db.collection('submissions').document(submission_id).update({
        "status": "Graded",
        "gradingFileURL": grading_pdf_url,
        "grade": extracted_mark,
        "feedback": grading_result
    })
    print(f"✅ Updated Firestore for submission {submission_id}")


def process_all_pending():
    print("🔍 Checking for multiple pending submissions...")
    submissions_ref = db.collection('submissions')\
        .where('status', '==', 'Pending')\
        .order_by('submittedAt', direction=firestore.Query.ASCENDING)\
        .limit(10)  # ✅ Process up to 10 students at once

    submission_docs = list(submissions_ref.stream())
    if not submission_docs:
        print("✅ No pending submissions. Waiting...")
        return

    for doc in submission_docs:
        try:
            process_submission(doc)
        except Exception as e:
            print(f"❌ Error processing {doc.id}: {e}")


if __name__ == "__main__":
    while True:
        try:
            process_all_pending()
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(10)  # Wait before next batch
