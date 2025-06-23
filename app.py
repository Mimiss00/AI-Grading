from flask import Flask, Blueprint, render_template, request, redirect, session, url_for, flash
from flask_bcrypt import Bcrypt
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'frontend', 'templates') 
STATIC_DIR = os.path.join(BASE_DIR, 'frontend', 'static')

print("Resolved template path:", TEMPLATE_DIR)
print("Templates:", os.listdir(TEMPLATE_DIR))

# --- Lecturer Blueprint ---
lecturer_bp = Blueprint('lecturer', __name__, template_folder=TEMPLATE_DIR)

@lecturer_bp.route('/login')
def login_lecturer():
    return render_template('signupEdu.html')

@lecturer_bp.route('/signup')
def signup_lecturer():
    return render_template('signupEdu.html')

@lecturer_bp.route('/dashboard-edu')
def dashboard_lecturer():
    return render_template('indexEdu.html')

@lecturer_bp.route('/my-classes')
def my_classes():
    return render_template('submissionEdu.html')

@lecturer_bp.route('/upload-material')
def upload_material():
    return render_template('uploadEdu.html')

@lecturer_bp.route('/all-assignment')
def all_assignment():
    return render_template('AssignmentsEdu.html')

# --- Student Blueprint ---
student_bp = Blueprint('student', __name__, template_folder=TEMPLATE_DIR)

@student_bp.route('/login', methods=['GET'])
def login_student():
    return render_template('login.html')

@student_bp.route('/dashboard', methods=['GET'])
def student_dashboard():
    return render_template("indexStud.html")

@student_bp.route('/my-assignment', methods=['GET'])
def student_assignment():
    return render_template('meetings.html')

@student_bp.route('/uploadAssignment', methods=['GET'])
def student_upload():
    return render_template('uploadStud.html')

@student_bp.route('/gradeStud', methods=['GET'])
def student_grade():
    return render_template('gradesStud.html')

# --- Flask App Setup ---
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

# Register Blueprints
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(lecturer_bp, url_prefix='/lecturer')

@app.route('/')
def role_select():
    return render_template('roleSelect.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use dynamic port for deployment platforms
    app.run(host="0.0.0.0", port=port)
