from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import datetime
import base64
import os
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secure-dev-fallback-key-123987')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

db_path = os.path.join(tempfile.gettempdir(), 'portfolio.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_name = db.Column(db.String(100), nullable=True)
    image_base64 = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def is_allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    is_admin = session.get('admin_logged_in', False)
    return render_template('index.html', posts=posts, is_admin=is_admin)

@app.route('/api/terminal', methods=['POST'])
def handle_terminal_api():
    data = request.get_json() or {}
    
    if 'password' in data:
        password_payload = data.get('password', '')
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if stored_hash and check_password_hash(stored_hash, password_payload):
            session['admin_logged_in'] = True
            return jsonify({
                "output": "<span style='color:#00ff00'>[SUCCESS] Signature verified. Session authenticated. Reloading environment...</span>", 
                "authenticated": True
            })
        return jsonify({"output": "<span style='color:#ff5555'>sudo: 3 incorrect password attempts</span>"})

    raw_input = data.get('command', '').strip()
    cmd = raw_input.lower()
    
    if cmd == 'sudo su' or cmd == 'ssh root@localhost':
        return jsonify({
            "output": "<span style='color:#fff;'>[sudo] password for admin: </span>", 
            "await_password": True
        })

    if cmd == "help":
        return jsonify({"output": "Available commands:<br>  <b>skills</b> - Display specialized domain profiles.<br>  <b>resume</b> - Read educational background details.<br>  <b>clear</b>  - Flush terminal screen log trace."})
    elif cmd == "skills":
        return jsonify({"output": "<span style='color:#00ffff'>Focus:</span> Web Security, Reverse Engineering, Form Input Hardening."})
    elif cmd == "resume":
        return jsonify({"output": "<b>Anshu Vishwakarma</b><br>Security Researcher & BCA Graduate."})
    elif cmd == "clear":
        return jsonify({"output": ""})
        
    return jsonify({"output": f"bash: {raw_input}: command not found"})

@app.route('/admin-action/publish', methods=['POST'])
def publish_entry():
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
        
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    file = request.files.get('image')
    
    b64_string = None
    clean_name = None

    if file and file.filename != '':
        if is_allowed_image(file.filename):
            from werkzeug.utils import secure_filename
            clean_name = secure_filename(file.filename)
            b64_string = base64.b64encode(file.read()).decode('utf-8')

    if title and content:
        new_post = BlogPost(title=title, content=content, image_name=clean_name, image_base64=b64_string)
        db.session.add(new_post)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/admin-action/delete/<int:post_id>', methods=['POST'])
def delete_entry(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403
        
    target_post = BlogPost.query.get_or_404(post_id)
    db.session.delete(target_post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/admin-action/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()
