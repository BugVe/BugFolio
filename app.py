from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Fallback configuration for production or local development environments
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model Schema
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    tech_stack = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True) # Direct Access/IDOR control protection

# Explicit Hardcoded Content Registry (Strictly kills file system access vectors)
SAFE_FILES = {
    "contact.txt": "Email     : you@email.com\nLocation  : Ghaziabad, UP, IN\nGitHub    : github.com/yourhandle\nHackerOne : hackerone.com/yourhandle <span style='color:#ff5555'>[ACTIVE]</span>",
    "summary.txt": "Aspiring penetration tester with hands-on bug bounty experience on Dell and Starbucks. Skilled in web application security, OWASP Top 10, and security hardening.",
    "bug_bounty/findings.log": "<span style='color:#ff5555'>[HIGH]</span> Dell — Subdomain Takeover\n└─ Identified vulnerability exposing infrastructure to hijacking.\n<span style='color:#ff5555'>[MEDIUM]</span> Starbucks — WAF Bypass\n└─ Bypassed active Web Application Firewall protections."
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/terminal', methods=['POST'])
def handle_terminal_api():
    data = request.get_json() or {}
    raw_input = data.get('command', '').strip()
    
    if not raw_input:
        return jsonify({"output": ""})

    parts = raw_input.split(maxsplit=1)
    base_cmd = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""

    # ---- CAT COMMAND LAYER (Protected against IDOR & Arbitrary Path Traversal) ----
    if base_cmd == "cat":
        if argument in SAFE_FILES:
            return jsonify({"output": SAFE_FILES[argument].replace('\n', '<br>')})
        return jsonify({"output": f"cat: {argument}: Permission denied or file structure access missing."})

    # ---- VIEW_PROJECT LAYER (Protected against SQL Injection via ORM Parameters & IDOR via column validation) ----
    elif base_cmd == "view_project":
        if not argument:
            return jsonify({"output": "Usage: view_project [project_name]<br>Example: view_project AuthBid"})
        
        # Secured completely from SQLi natively by parameterization layers in SQLAlchemy
        # Enforces object access check (is_public=True) to prevent guessing of hidden project scopes
        project = Project.query.filter_by(name=argument, is_public=True).first()
        
        if project:
            return jsonify({
                "output": f"Project: {project.name} [{project.tech_stack}]<br>└─ {project.description}"
            })
        return jsonify({"output": f"Error: Project '{argument}' restricted or non-existent."})

    # ---- LS COMMAND LAYER ----
    elif base_cmd == "ls":
        if argument == "skills/":
            return jsonify({"output": "<span style='color:#00ffff'>languages/</span><br>  Python, SQL, Java, C++<br><span style='color:#00ffff'>tools/</span><br>  Burp Suite, Wireshark, Subfinder, Kali Linux"})
        elif argument == "projects/":
            return jsonify({"output": "<span style='color:#00ffff'>AuthBid/</span> [Python, SQL]<br><span style='color:#00ffff'>SportsConnect/</span> [Python, SQL]<br><br>Type 'view_project [name]' to see execution details."})
        else:
            return jsonify({"output": "skills/&nbsp;&nbsp;&nbsp;&nbsp;projects/&nbsp;&nbsp;&nbsp;&nbsp;contact.txt&nbsp;&nbsp;&nbsp;&nbsp;summary.txt&nbsp;&nbsp;&nbsp;&nbsp;bug_bounty/"})

    # ---- HELP COMMAND LAYER ----
    elif base_cmd == "help":
        return jsonify({"output": "Available commands:<br>  ls<br>  ls skills/<br>  ls projects/<br>  cat contact.txt<br>  cat summary.txt<br>  cat bug_bounty/findings.log<br>  view_project [name]<br>  clear"})

    return jsonify({"output": f"bash: command not found: {base_cmd}"})

# Production initialization script
with app.app_context():
    db.create_all()
    if not Project.query.first():
        db.session.add(Project(name="AuthBid", tech_stack="Python, SQL", description="Token-based secure marketplace engine built to neutralize top OWASP web threats.", is_public=True))
        db.session.add(Project(name="SportsConnect", tech_stack="Python, SQL", description="Location-aware local player discovery platform utilizing parameterized input validation queries.", is_public=True))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
