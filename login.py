from flask import Blueprint, render_template

student_bp = Blueprint('student', __name__)

# 🔽 Add this route
@student_bp.route('/login', methods=['GET'])
def login_student():
    return render_template('login.html')


@student_bp.route('/dashboard', methods=['GET'])
def student_dashboard():
    return render_template("edu-meeting/indexStud.html")  # ✅

@student_bp.route('/my-assignment', methods=['GET'])
def student_assignment():
    return render_template('edu-meeting/meetings.html')


@student_bp.route('/uploadAssignment', methods=['GET'])
def student_upload():
    return render_template('uploadStud.html')


@student_bp.route('/gradeStud', methods=['GET'])
def student_grade():
    return render_template('gradesStud.html')



