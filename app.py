from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import os
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secure-dev-fallback-key-123987')

# Limit upload payloads to 2MB maximum to stop Denial of Service (DoS) attempts
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

db_path = os.path.join(tempfile.gettempdir(), 'portfolio.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_name = db.Column(db.String(100), nullable=True)  # Simple clean name track
    image_base64 = db.Column(db.Text, nullable=True)       # Image converted to safe string text
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def is_allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── PUBLIC PORTFOLIO ENGINE ───
@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('index.html', posts=posts, view_mode='public')

# Strict Whitelisted Terminal Loop (No other inputs process)
@app.route('/api/terminal', methods=['POST'])
def handle_terminal_api():
    data = request.get_json() or {}
    raw_input = data.get('command', '').strip().lower()
    
    ALLOWED_COMMANDS = ['help', 'skills', 'resume', 'clear']
    if not raw_input or raw_input not in ALLOWED_COMMANDS:
        return jsonify({"output": "bash: command executed is unrecognized or access parameters are restricted."})

    if raw_input == "help":
        return jsonify({"output": "Available options:<br>  <b>skills</b> - Display my technical security stack<br>  <b>resume</b> - Output career profile background<br>  <b>clear</b>  - Flush terminal screen memory"})
    elif raw_input == "skills":
        return jsonify({"output": "<span style='color:#00ffff'>Languages:</span> Python, SQL, Bash<br><span style='color:#00ffff'>Focus:</span> Web Security Architecture, Safe Input Parsing Controls."})
    elif raw_input == "resume":
        return jsonify({"output": "<b>Anshu Vishwakarma</b><br>Security Researcher & BCA Graduate.<br>Specialized in building input-validated defense frameworks."})
    return jsonify({"output": ""})


# ─── SECURE ADMIN PATHS (COMBINED INTO ONE HTML TEMPLATE) ───
@app.route('/admin-gateway', methods=['GET', 'POST'])
def admin_gateway():
    if request.method == 'POST':
        password = request.form.get('password')
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if stored_hash and check_password_hash(stored_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard_view'))
        return render_template('index.html', view_mode='admin_auth', error="Access Refused: Token mismatch.")
        
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard_view'))
    return render_template('index.html', view_mode='admin_auth')


@app.route('/admin-gateway/dashboard', methods=['GET', 'POST'])
def admin_dashboard_view():
    # Anti-IDOR Check: Server session must be validated before access is granted
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_gateway'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        file = request.files.get('image')
        
        b64_string = None
        clean_name = None

        if file and file.filename != '':
            if is_allowed_image(file.filename):
                # Simple name processing with clean characters, no path paths allowed
                clean_name = secure_filename(file.filename)
                
                # Convert the image bytes directly into a plain text base64 string
                # This completely strips out the server execution context
                file_bytes = file.read()
                b64_string = base64.b64encode(file_bytes).decode('utf-8')
            else:
                posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
                return render_template('index.html', view_mode='admin_dashboard', posts=posts, error="Extension rejected.")

        if title and content:
            new_post = BlogPost(title=title, content=content, image_name=clean_name, image_base64=b64_string)
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('admin_dashboard_view'))
            
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('index.html', view_mode='admin_dashboard', posts=posts)


@app.route('/admin-gateway/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    # Strict server verification to block broken object level modifications
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Action refused: State context invalid."}), 403
        
    target_post = BlogPost.query.get_or_404(post_id)
    db.session.delete(target_post)
    db.session.commit()
    return redirect(url_for('admin_dashboard_view'))


@app.route('/admin-gateway/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import datetime
import base64
import os
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secure-dev-fallback-key-123987')

# Mitigate DoS space exhaustion vectors by limiting incoming data streams to 2MB
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


# ─── SECURE LINUX-STYLE STEALTH TERMINAL AUTH LOOP ───
@app.route('/api/terminal', methods=['POST'])
def handle_terminal_api():
    data = request.get_json() or {}
    
    # PHASE 2: Handle the blind password packet sent directly after the trigger command
    if 'password' in data:
        password_payload = data.get('password', '')
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if stored_hash and check_password_hash(stored_hash, password_payload):
            session['admin_logged_in'] = True
            return jsonify({
                "output": "<span style='color:#00ff00'>[SUCCESS] Signature payload valid. Relocating matrix states...</span>", 
                "authenticated": True
            })
        return jsonify({"output": "<span style='color:#ff5555'>sudo: 3 incorrect password attempts</span>"})

    # PHASE 1: Handle standard commands and the custom stealth trigger entry
    raw_input = data.get('command', '').strip()
    cmd = raw_input.lower()
    
    # Your completely unlisted administrative trigger door command
    if cmd == 'sudo su' or cmd == 'ssh root@localhost':
        return jsonify({
            "output": "<span style='color:#fff;'>[sudo] password for admin: </span>", 
            "await_password": True
        })

    if cmd == "help":
        return jsonify({"output": "Available lookups:<br>  <b>skills</b> - Display background engineering profile stacks.<br>  <b>resume</b> - Read educational pathway archives.<br>  <b>clear</b>  - Flush visual shell screen logging trackers."})
    elif cmd == "skills":
        return jsonify({"output": "<span style='color:#00ffff'>Focus:</span> Web App Hardening, Injection Suppression, Advanced Input State Processing Controls."})
    elif cmd == "resume":
        return jsonify({"output": "<b>Anshu Vishwakarma</b><br>Security Researcher & BCA Graduate.<br>Specialized in zero-trust logic development models."})
    elif cmd == "clear":
        return jsonify({"output": ""})
        
    return jsonify({"output": f"bash: {raw_input}: command unrecognized or privilege level restricted."})


# ─── SECURE INGESTION ENDPOINTS (PROTECTED AGAINST IDOR PARAMETERS) ───
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
            # Binary string mapping completely breaks RCE scripts execution vectors
            b64_string = base64.b64encode(file.read()).decode('utf-8')

    if title and content:
        # Jinja context keeps inputs interpreted safely as literal plain text string tags
        new_post = BlogPost(title=title, content=content, image_name=clean_name, image_base64=b64_string)
        db.session.add(new_post)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/admin-action/delete/<int:post_id>', methods=['POST'])
def delete_entry(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Action refused: Invalid session token access signatures."}), 403
        
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
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import datetime
import base64
import os
import tempfile

app = Flask(__name__)
# Cryptographically signs cookies. Must be a strong random secret key string in production environment
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secure-dev-fallback-key-123987')

# Mitigate DoS space exhaustion vectors by limiting database stream sizing to 2MB
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

# ─── SINGLE UNIFIED URL CONTROLLER ───
@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    # Read admin token authorization state from encrypted cookie context
    is_admin = session.get('admin_logged_in', False)
    return render_template('index.html', posts=posts, is_admin=is_admin)


# ─── NATIVE TERMINAL INTERFACE WITH HIDDEN AUTH LOOP ───
@app.route('/api/terminal', methods=['POST'])
def handle_terminal_api():
    data = request.get_json() or {}
    raw_input = data.get('command', '').strip()
    
    # 🔐 TERMINAL PRIVILEGE ESCALATION ENGINE
    if raw_input.lower().startswith('su') :
        password_payload = raw_input[5:].strip()
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if stored_hash and check_password_hash(stored_hash, password_payload):
            session['admin_logged_in'] = True
            return jsonify({
                "output": "<span style='color:#00ff00'>[SUCCESS] Cryptographic signature accepted. Upgrading environment context...</span>", 
                "authenticated": True
            })
        return jsonify({"output": "<span style='color:#ff5555'>[FAILURE] Access denied: Invalid administrative signature key.</span>"})

    # Regular Whitelisted Operations
    cmd = raw_input.lower()
    if cmd == "help":
        return jsonify({"output": "Available commands:<br>  <b>skills</b> - Look up engineering stack profiles.<br>  <b>resume</b> - Read background information data.<br>  <b>clear</b>  - Flush command history tracking logs."})
    elif cmd == "skills":
        return jsonify({"output": "<span style='color:#00ffff'>Focus:</span> Web Security Architecture, Code Injection Mitigation, Secure Authentication Logic Models."})
    elif cmd == "resume":
        return jsonify({"output": "<b>Anshu Vishwakarma</b><br>Security Engineer & BCA Graduate.<br>Specialized in zero-trust input styling architectures."})
    elif cmd == "clear":
        return jsonify({"output": ""})
        
    return jsonify({"output": "bash: command executed is unrecognized or access parameters are restricted."})


# ─── SECURE ADMINISTRATIVE WRITING ENDPOINTS (ANTI-IDOR GATEKEEPERS) ───
@app.route('/admin-action/publish', methods=['POST'])
def publish_entry():
    # Strict Server-Side Session check completely neutralizes IDOR attempts
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
            # Binary translation to Base64 plaintext kills script execution completely
            b64_string = base64.b64encode(file.read()).decode('utf-8')

    if title and content:
        # Jinja context ensures everything saved renders back safely strictly as flat text strings
        new_post = BlogPost(title=title, content=content, image_name=clean_name, image_base64=b64_string)
        db.session.add(new_post)
        db.session.commit()
        
    return redirect(url_for('index'))


@app.route('/admin-action/delete/<int:post_id>', methods=['POST'])
def delete_entry(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Action blocked: Insufficient security states."}), 403
        
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
