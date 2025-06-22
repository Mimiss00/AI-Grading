from flask import Flask, Blueprint, render_template, request, redirect, session, url_for, flash
from flask_bcrypt import Bcrypt
import os

lecturer_bp = Blueprint('lecturer', __name__, template_folder='templates')

@lecturer_bp.route('/login')
def login_lecturer():
    return render_template('signupEdu.html')

@lecturer_bp.route('/signup')
def signup_lecturer():
    return render_template('signupEdu.html')

@lecturer_bp.route('/dashboard-edu')
def dashboard_lecturer():
    return render_template('edu-meeting/indexEdu.html')

@lecturer_bp.route('/my-classes')
def my_classes():
    return render_template('edu-meeting/submissionEdu.html')

@lecturer_bp.route('/upload-material')
def upload_material():
    return render_template('uploadEdu.html')

@lecturer_bp.route('/all-assignment')
def all_assignment():
    return render_template('edu-meeting/AssignmentsEdu.html')
