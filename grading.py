import os
import io
import json
import urllib.parse
import requests
import openai
import re
from fpdf import FPDF
from PyPDF2 import PdfMerger
from firebase_admin import credentials, initialize_app, firestore, storage

# ========== CONFIGURATION ==========
openai_api_key = "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"  # Replace with your real OpenAI API Key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ocr-pipeline/fyp-ai-3a972-firebase-adminsdk-fbsvc-7f58918799.json"

extracted_answers_folder = "extracted_answers"
grading_results_folder = "grading_results"
os.makedirs(grading_results_folder, exist_ok=True)

# Initialize Firebase
cred = credentials.Certificate("ocr-pipeline/fyp-ai-3a972-firebase-adminsdk-fbsvc-7f58918799.json")
initialize_app(cred, {'storageBucket': 'fyp-ai-3a972.firebasestorage.app'})  # Use 'appspot.com' NOT 'firebasestorage.app'
db = firestore.client()

# ========== FUNCTION TO DOWNLOAD FILE ==========
def download_file(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {save_path}")
    else:
        raise Exception(f"Failed to download file from {url}")

# ========== MAIN ==========
def main():
    print("\n🚀 Fetching latest student submission...")

    # Get latest submission
    submissions_ref = db.collection('submissions').order_by('submittedAt', direction=firestore.Query.DESCENDING).limit(1)
    submission_docs = list(submissions_ref.stream())

    if not submission_docs:
        print("❌ No submissions found.")
        return

    submission_doc = submission_docs[0]
    submission = submission_doc.to_dict()
    submission_id = submission_doc.id

    file_url = submission.get("fileURL")
    assignment_id = submission.get("assignmentId")

    if not file_url or not assignment_id:
        print("❌ Submission missing fileURL or assignmentId.")
        return

    print(f"📄 Assignment ID: {assignment_id}")

    # Fetch assignment
    assignment_doc = db.collection('assignments').document(assignment_id).get()
    if not assignment_doc.exists:
        print("❌ Assignment not found!")
        return
    assignment = assignment_doc.to_dict()
    answer_scheme_url = assignment.get("answerSchemeFileURL")

    if not answer_scheme_url:
        print("❌ Answer scheme not available for this assignment.")
        return

    # Download student's original handwritten PDF
    file_name = os.path.basename(urllib.parse.unquote(file_url.split('/o/')[1].split('?')[0]))
    student_pdf_path = "temp_student.pdf"
    download_file(file_url, student_pdf_path)

    # Load student's extracted answers
    extracted_json_path = os.path.join(extracted_answers_folder, file_name.replace(".pdf", ".json"))

    if not os.path.exists(extracted_json_path):
        print(f"❌ Extracted file not found: {extracted_json_path}")
        return

    with open(extracted_json_path, "r", encoding="utf-8") as f:
        extracted_data = json.load(f)

    student_cpp_code = extracted_data.get("rawText", "")

    if not student_cpp_code.strip():
        print("❌ Extracted student answer is empty.")
        return

    # Download lecturer's answer scheme
    answer_scheme_save_path = "temp_answer_scheme.json"
    download_file(answer_scheme_url, answer_scheme_save_path)

    with open(answer_scheme_save_path, "r", encoding="utf-8") as f:
        lecturer_answer_scheme = f.read()

    # ========== Call OpenAI for Grading ==========
    client = openai.OpenAI(api_key=openai_api_key)

    print("\n🧠 Asking OpenAI for grading...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a strict C++ programming lecturer. Grade the student's C++ assignment based on the given answer scheme. Give marks and short feedback."},
            {"role": "user", "content": f"Answer Scheme:\n{lecturer_answer_scheme}\n\nStudent Submission:\n{student_cpp_code}\n\nPlease give a grade over 100 marks and personalized feedback."}
        ],
        temperature=0.2
    )

    grading_result = response.choices[0].message.content

    # Save grading result into a temp PDF
    feedback_pdf_path = "temp_feedback.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in grading_result.split("\n"):
        pdf.multi_cell(0, 10, line)

    pdf.output(feedback_pdf_path)

    # ========== Merge Student PDF + Grading PDF ==========
    final_pdf_path = os.path.join(grading_results_folder, file_name.replace(".pdf", "_grading_final.pdf"))
    merger = PdfMerger()
    merger.append(student_pdf_path)
    merger.append(feedback_pdf_path)
    merger.write(final_pdf_path)
    merger.close()

    print(f"✅ Merged PDF created: {final_pdf_path}")

    # ========== Upload Merged PDF to Firebase ==========
    bucket = storage.bucket()
    blob = bucket.blob(f'grading_results/{os.path.basename(final_pdf_path)}')
    blob.upload_from_filename(final_pdf_path)
    blob.make_public()

    grading_pdf_url = blob.public_url
    print(f"✅ Uploaded to Firebase: {grading_pdf_url}")

    # ========== Extract Marks from grading result ==========
    mark_match = re.search(r"(\d{1,3})\s*/\s*100", grading_result)
    if mark_match:
        extracted_mark = f"{mark_match.group(1)}/100"
        print(f"✅ Extracted Mark: {extracted_mark}")
    else:
        extracted_mark = "-"
        print("⚠️ No mark found in grading result.")

    # ========== Update Firestore ==========
    db.collection('submissions').document(submission_id).update({
       "gradingFileURL": grading_pdf_url,
        "status": "Graded",
        "grade": extracted_mark
    })

    print(f"✅ Submission {submission_id} updated with grade and feedback PDF.")

# ========== RUN ==========
if __name__ == "__main__":
    main()
