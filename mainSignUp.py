
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from login import student_bp
from signupEdu import lecturer_bp


app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)


# Register Blueprints
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(lecturer_bp, url_prefix='/lecturer')

@app.route('/')
def role_select():
    return render_template('roleSelect.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))  # Render provides PORT dynamically
    app.run(host="0.0.0.0", port=port)

