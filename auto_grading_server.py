
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
import traceback  
from openai import OpenAI  
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PyPDF2 import PdfReader, PdfWriter



# ========== CONFIGURATION ==========
# Set your API keys and JSON paths
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fyp-ai-3a972-OCR_API.json"  # Google Vision API
openai_api_key = "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"  # <-- Put your OpenAI API Key here

# Initialize Firebase
cred = credentials.Certificate("fyp-ai-3a972-firebase-adminsdk-fbsvc-7f58918799.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'fyp-ai-3a972.firebasestorage.app'})
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
    text = re.sub(r"GS CamScanner", "", text)
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


def generate_grading_prompt(answer_scheme: str, student_answer: str, total_marks: int = 10):
    def is_inline_scheme(text):
        return any("mark" in line.lower() for line in text.splitlines() if "//" in line or "mark" in line)

    if is_inline_scheme(answer_scheme):
        system_prompt = (
            "You are a strict but fair C++ programming lecturer.\n"
            "Grade the student's code based on the inline-annotated model answer provided.\n"
            "- The model answer includes inline comments (e.g., '1 mark', '0.5 marks').\n"
            "- IMPORTANT: First check if the student's code is solving the same problem.\n"
            "  - If the logic is unrelated (e.g., solving vacation logic instead of commission), award 0/total marks and explain.\n"
            "- Do not award marks for includes, variable declarations, or correct syntax if the logic is not aligned with the model answer.\n"
            "- For each student line, provide feedback:\n"
            "  Line N | student code // Correct (X marks) OR // Incorrect - reason (0 marks)\n"
            f"- Finish with 'Overall Score: X/{total_marks}' and Final Feedback."
        )
    else:
        system_prompt = (
            "You are a strict but fair C++ programming lecturer grading C++ submissions.\n"
            f"Marking Scheme (Total: {total_marks} marks):\n"
            "- Variable declarations (only if relevant to the problem): 1 mark\n"
            "- Prompt and input statements (only if relevant): 1 mark\n"
            "- Correct use of logic solving the same problem: 4 marks\n"
            "- Output/display statements (only if aligned to the task): 2 marks\n"
            "- Structure and syntax: 2 marks\n\n"
            "IMPORTANT:\n"
            "- First, check if the student is solving the same problem as the model answer.\n"
            "  - If not, award 0 marks for logic, input/output, and variables.\n"
            "- Do not give any marks for syntactically correct but irrelevant lines.\n"
            "- Do not assume the question. Grade strictly based on the task described in the model answer.\n\n"
            "For each line, use this format:\n"
            "  Line N | code // Correct (X marks) OR // Incorrect - explanation (0 marks)\n"
            f"Then conclude with 'Overall Score: X/{total_marks}' and Final Feedback."
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Model Answer:\n{answer_scheme.strip()}\n\nStudent Submission:\n{student_answer.strip()}\n\nGrade this based on the model answer only. Award 0 if unrelated."}
    ]





def ask_openai_grading(answer_scheme, student_answer):
    client = OpenAI(api_key=openai_api_key)

    student_lines = student_answer.strip().split('\n')
    numbered_student_answer = "\n".join([f"{idx+1} | {line}" for idx, line in enumerate(student_lines)])
    total_marks = extract_total_marks(answer_scheme)

    messages = generate_grading_prompt(answer_scheme, numbered_student_answer, total_marks)
    
    # ✅ DEBUG: Show which prompt is being sent
    print("🔍 Prompt sent to OpenAI:")
    for m in messages:
        print(f"[{m['role'].upper()}] {m['content']}\n{'-'*60}")

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





def extract_first_page(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

# Merge PDFs
def merge_pdfs(pdf_paths, output_path):
    merger = PdfMerger()
    for path in pdf_paths:
        merger.append(path)
    merger.write(output_path)
    merger.close()

def convert_image_to_pdf(image_path, output_pdf_path):
    from PIL import Image
    image = Image.open(image_path).convert("RGB")
    image.save(output_pdf_path, "PDF", resolution=100.0)


# ========== MAIN PROCESS ==========
def process_submission(submission_doc):
    submission_id = submission_doc.id
    submission = submission_doc.to_dict()

    file_url = submission.get("fileURL")
    assignment_id = submission.get("assignmentId")
    if not file_url or not assignment_id:
        print(f"❌ Missing fileURL or assignmentId for {submission_id}.")
        return

    assignment_doc = db.collection('assignments').document(assignment_id).get()
    if not assignment_doc.exists:
        print(f"❌ Assignment not found for {assignment_id}")
        return

    assignment = assignment_doc.to_dict()
    answer_scheme_url = assignment.get("answerSchemeFileURL")
    if not answer_scheme_url:
        print("❌ No answer scheme available.")
        return

    # Download and OCR student PDF
    parsed_path = file_url.split('/o/')[1].split('?')[0]
    storage_path = urllib.parse.unquote(parsed_path)
    local_student_pdf = f"/tmp/{submission_id}_{os.path.basename(storage_path)}"
    bucket.blob(storage_path).download_to_filename(local_student_pdf)

    images = convert_from_path(local_student_pdf, dpi=400, poppler_path=POPPLER_PATH)
    all_text = ""
    for i, page in enumerate(images):
        print(f"🖼️ Processing page {i+1}...")
        img_bytes = image_to_bytes(preprocess_image(page))
        all_text += clean_cpp_code(run_google_ocr(img_bytes)) + "\n"

    # Download answer scheme
    parsed_ans = answer_scheme_url.split('/o/')[1].split('?')[0]
    ans_path = urllib.parse.unquote(parsed_ans)
    local_answer_json = "/tmp/answer_scheme.json"
    bucket.blob(ans_path).download_to_filename(local_answer_json)
    with open(local_answer_json, "r", encoding="utf-8") as f:
        answer_scheme = f.read()

    # Grading
    grading_result = ask_openai_grading(answer_scheme, all_text)
    print("📄 Grading Result:\n", grading_result)

# After grading_result and submission_id have been defined earlier in your function:





    # Generate feedback PDF
    feedback_pdf_path = f"/tmp/{submission_id}_feedback.pdf"
    if os.path.exists(feedback_pdf_path):
        os.remove(feedback_pdf_path)
    create_feedback_pdf(grading_result, feedback_pdf_path)

    # Try to add student image first
    student_image_path = f"/path/to/images/{submission_id}.png"  # ← Replace with actual image location
    student_image_pdf = f"/tmp/{submission_id}_original_submission.pdf"

    if os.path.exists(student_image_path):
        convert_image_to_pdf(student_image_path, student_image_pdf)
        pdfs_to_merge = [student_image_pdf, feedback_pdf_path]
    else:
        pdfs_to_merge = [feedback_pdf_path]

    # ✅ This must NOT be indented into the `else` block
    final_pdf_path = f"/tmp/{submission_id}_grading_final.pdf"
    merge_pdfs([local_student_pdf, feedback_pdf_path], final_pdf_path)




    # Upload to Firebase Storage
    grading_blob = bucket.blob(f'grading_results/{submission_id}_grading_final.pdf')
    grading_blob.upload_from_filename(final_pdf_path)
    grading_blob.make_public()

    # Add timestamp to avoid browser caching
    timestamp = int(time.time())
    grading_pdf_url = grading_blob.public_url + f"?v={timestamp}"
    print("✅ Uploaded latest grading PDF to Firebase.")
    print(f"📄 URL: {grading_pdf_url}")
    print(f"📦 PDF Size: {os.path.getsize(final_pdf_path)} bytes")

    # Extract score from grading result
    match = re.findall(r"Overall Score:\s*(\d{1,3})\s*/\s*(\d{1,3})", grading_result)
    score = f"{match[-1][0]}/{match[-1][1]}" if match else "-"

    # Update Firestore
    db.collection('submissions').document(submission_id).update({
        "status": "Graded",
        "gradingFileURL": grading_pdf_url,
        "grade": score,
        "feedback": grading_result
    })
    print(f"✅ Uploaded and updated Firestore for {submission_id}")




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
from textwrap import wrap


def create_feedback_pdf(text, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style with monospaced font
    monospace_style = ParagraphStyle(
        'Monospace',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=12,
        leading=14,
        spaceAfter=6
    )
    
    content = []
    for line in text.split('\n'):
        # Set color based on correctness
        if "// Incorrect" in line:
            color = "red"
        elif "// Correct" in line:
            color = "green"
        else:
            color = "black"
            
        # Create styled paragraph with color
        styled_text = f'<font color="{color}">{line}</font>'
        content.append(Paragraph(styled_text, monospace_style))
    
    doc.build(content)



if __name__ == "__main__":
    while True:
        try:
            process_all_pending()
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(10)  # Wait before next batch
