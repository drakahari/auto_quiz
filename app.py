from flask import Flask, send_from_directory, request, redirect, render_template_string
import os, re, json, time

app = Flask(__name__, static_folder=".", static_url_path="")

# =========================
# PATH SETUP
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
QUIZ_FOLDER = os.path.join(BASE_DIR, "quizzes")
CONFIG_FOLDER = os.path.join(BASE_DIR, "config")
LOGO_FOLDER = os.path.join(BASE_DIR, "static", "logos")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(QUIZ_FOLDER, exist_ok=True)
os.makedirs(CONFIG_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

PORTAL_CONFIG = os.path.join(CONFIG_FOLDER, "portal.json")
QUIZ_REGISTRY = os.path.join(CONFIG_FOLDER, "quizzes.json")


# =========================
# Auto Logo Removal
# =========================
def cleanup_temp_logos(max_age_minutes=30):
    now = time.time()

    for fname in os.listdir(LOGO_FOLDER):
        if not fname.startswith("temp_logo_"):
            continue

        path = os.path.join(LOGO_FOLDER, fname)

        try:
            stat = os.stat(path)
            age_minutes = (now - stat.st_mtime) / 60

            if age_minutes > max_age_minutes:
                os.remove(path)
                print(f"[CLEANUP] Removed abandoned temp logo: {fname}")

        except Exception as e:
            print(f"[CLEANUP ERROR] {fname}: {e}")



# =========================
# PORTAL CONFIG MANAGEMENT
# =========================
def load_portal_config():
    default = {
        "title": "Training & Practice Center",
        "show_confidence": True,
        "enable_regex_strip": False
    }

    if not os.path.exists(PORTAL_CONFIG):
        return default

    try:
        with open(PORTAL_CONFIG, "r") as f:
            data = json.load(f)

            if not isinstance(data, dict):
                return default

            return {
                "title": data.get("title", default["title"]),
                "show_confidence": data.get("show_confidence", default["show_confidence"]),
                "enable_regex_strip": data.get("enable_regex_strip", default["enable_regex_strip"]),
            }

    except Exception:
        return default



def save_portal_config(title, show_confidence=True, enable_regex_strip=False):
    cfg = {
        "title": title,
        "show_confidence": show_confidence,
        "enable_regex_strip": enable_regex_strip
    }


    with open(PORTAL_CONFIG, "w") as f:
        json.dump(cfg, f, indent=4)


def get_portal_title():
    return load_portal_config().get("title", "Training & Practice Center")


def get_confidence_setting():
    return load_portal_config().get("show_confidence", True)



# =========================
# QUIZ REGISTRY
# =========================
def load_registry():
    if not os.path.exists(QUIZ_REGISTRY):
        return []
    try:
        with open(QUIZ_REGISTRY, "r") as f:
            return json.load(f)
    except:
        return []


def save_registry(registry):
    with open(QUIZ_REGISTRY, "w") as f:
        json.dump(registry, f, indent=4)


def add_quiz_to_registry(html_name, quiz_title, logo_filename):
    registry = load_registry()
    registry.append({
        "html": html_name,
        "title": quiz_title,
        "logo": logo_filename,
        "timestamp": int(time.time())
    })
    save_registry(registry)


# =========================
# ROOT + STATIC (ORDER MATTERS)
# =========================

@app.route("/")
def home():
    portal_title = get_portal_title()

    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()

    return render_template_string(html, portal_title=portal_title)


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(DATA_FOLDER, filename)


@app.route("/quizzes/<path:filename>")
def serve_quiz(filename):
    return send_from_directory(QUIZ_FOLDER, filename)


@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(".", path)


# =========================
# DELETE QUIZ
# =========================
@app.route("/delete_quiz/<html_name>", methods=["POST"])
def delete_quiz(html_name):
    registry = load_registry()
    updated = []
    json_file_to_delete = None
    logo_to_delete = None

    for q in registry:
        if q["html"] == html_name:
            try:
                json_file_to_delete = q["html"].replace(".html", ".json")
            except:
                pass
            logo_to_delete = q.get("logo")
            continue
        updated.append(q)

    save_registry(updated)

    html_path = os.path.join(QUIZ_FOLDER, html_name)
    if os.path.exists(html_path):
        os.remove(html_path)

    if json_file_to_delete:
        json_path = os.path.join(DATA_FOLDER, json_file_to_delete)
        if os.path.exists(json_path):
            os.remove(json_path)

    if logo_to_delete:
        lp = os.path.join(LOGO_FOLDER, logo_to_delete)
        if os.path.exists(lp):
            os.remove(lp)

    return redirect("/library")


# =========================
# SAVE ORDER (DRAG + DROP)
# =========================
@app.route("/save_order", methods=["POST"])
def save_order():

    data = request.get_json()
    order = data.get("order", [])

    registry = load_registry()

    lookup = {q["html"]: q for q in registry}
    new_list = []

    for html in order:
        if html in lookup:
            new_list.append(lookup.pop(html))

    new_list.extend(lookup.values())
    save_registry(new_list)

    return {"status": "ok"}


# =========================
# LIBRARY (WITH DRAG + DROP!)
# =========================
@app.route("/library")
def quiz_library():
    quizzes = load_registry()
    portal_title = get_portal_title()

    return render_template_string("""
    <html>
    <head>
        <title>Quiz Library</title>
        <link rel="stylesheet" href="/style.css">

        <!-- Drag + Drop Library -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            {{portal_title}}<br>
            <span style="font-size:22px;opacity:.85">📚 Quiz Library</span>
        </h1>

        <div class="card">

            {% if quizzes %}
                <h2>Drag to Reorder</h2>

                <div id="quizList">

                {% for q in quizzes %}
                <div class="quiz-card"
                     data-id="{{q['html']}}"
                     style="
                        padding:14px;
                        margin:10px;
                        background:rgba(0,0,0,.6);
                        border-radius:8px;
                        display:flex;
                        justify-content:space-between;
                        gap:20px;
                        cursor:grab;
                     ">

                    <div style="flex:1;">
                        <h3 style="
                            margin-top:0;
                            margin-bottom:6px;
                            font-size:24px;
                            font-weight:900;
                            letter-spacing:.5px;">
                            {{q['title']}}
                        </h3>

                        <div style="margin-top:10px;">
                            <button onclick="location.href='/quizzes/{{q['html']}}'"
                                    style="padding:8px 14px; border-radius:6px;">
                                ▶ Open Quiz
                            </button>
                        </div>
                    </div>

                    <div style="
                        width:150px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                        align-items:center;
                    ">

                        {% if q.get('logo') %}
                        <img src="/static/logos/{{q['logo']}}"
                             style="max-height:90px; width:auto;">
                        {% else %}
                        <div style="height:90px;"></div>
                        {% endif %}

                        <form method="POST"
                              action="/delete_quiz/{{q['html']}}"
                              onsubmit="return confirm('Delete this quiz permanently?');"
                              style="margin-top:12px; width:100%; text-align:center;">

                            <button type="submit" style="
                                width:100%;
                                background:#7a0000;
                                color:white;
                                border:none;
                                padding:7px 0;
                                font-size:13px;
                                border-radius:6px;
                                cursor:pointer;">
                                🗑 Delete
                            </button>
                        </form>

                    </div>
                </div>
                {% endfor %}
                </div>

            {% else %}
                <p>No quizzes created yet. Upload one 😊</p>
            {% endif %}

            <br>
            <button onclick="location.href='/upload'">📤 Upload New Quiz</button>
            <button onclick="location.href='/paste'">📋 Paste Questions Instead</button>
                      
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>

    </div>

<script>
const list = document.getElementById("quizList");

Sortable.create(list, {
    animation: 150,
    handle: ".quiz-card",
    onEnd: () => {
        const order = [...document.querySelectorAll(".quiz-card")]
            .map(card => card.getAttribute("data-id"));

        fetch("/save_order", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ order })
        });
    }
});
</script>

    </body>
    </html>
    """, quizzes=quizzes, portal_title=portal_title)



# =========================
# UPLOAD PAGE
# =========================
@app.route("/upload")
def upload_page():
    portal_title = get_portal_title()

    return render_template_string(f"""
    <html>
    <head>
        <title>Upload Quiz File</title>
        <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            📤 Create a New Quiz
        </h1>

        <div class="card">

            <h2>Option 1 — Upload a Text File</h2>
            <p style="opacity:.8">
                Use this if you already have a .txt question file.
            </p>

            <form action="/process" method="POST" enctype="multipart/form-data">

                <h3>Quiz Display Title</h3>
                <input type="text" name="quiz_title"
                       placeholder="Example: Cloud+ Networking Practice"
                       required style="width:100%;padding:6px">

                <br><br>

                <h3>Select Quiz Text File</h3>
                <p style="opacity:.7; font-size:12px">
                    Upload any properly formatted .txt file
                </p>

                <input type="file" name="file" accept=".txt" required>

                <br><br>

                <h3>Upload Logo (Optional)</h3>
                <input type="file" name="quiz_logo" accept="image/*">
                <p style="opacity:0.7; font-size:12px">
                    Supported: PNG / JPG / GIF
                </p>

                <button type="submit">📤 Upload & Build Quiz</button>
            </form>


            <hr style="margin:25px 0; opacity:.5">


            <h2>Option 2 — Paste Questions Instead</h2>
            <p style="opacity:.8">
                Use this if you do NOT have a .txt file. Just paste your questions.
            </p>

            <button onclick="location.href='/paste'">
                📋 Paste Questions to Build Quiz
            </button>

            <br><br>
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>
    </div>
    </body>
    </html>
    """)



# =========================
# PASTE QUIZ PAGE
# =========================
@app.route("/paste")
def paste_page():
    portal_title = get_portal_title()

    return render_template_string("""
    <html>
    <head>
        <title>Paste Quiz Questions</title>
        <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            📋 Create Quiz From Pasted Text
        </h1>

        <div class="card">

            <!-- IMPORTANT: Goes to PREVIEW first -->
            <form action="/preview_paste" method="POST" enctype="multipart/form-data">

                <h3>Quiz Display Title</h3>
                <input type="text" name="quiz_title"
                       placeholder="Example: Linux+ Practice Set"
                       required style="width:100%; padding:6px">

                <br><br>

                <h3>Paste Questions + Answers</h3>
                <p style="opacity:.8; font-size:12px">
                    Supports formats like:<br>
                    1. Question text<br>
                    A. Answer<br>
                    B. Answer<br>
                    C. Answer<br>
                    Suggested Answer: B
                </p>

                <textarea name="quiz_text"
                          required
                          style="width:100%; height:400px; padding:10px; font-size:14px;"></textarea>

                <br><br>

                <h3>Optional: Remove Unwanted Text Before Parsing</h3>
                <p style="opacity:.8; font-size:12px">
                    Any line containing these values will be automatically deleted.<br>
                    (One per line, case insensitive)
                </p>

                <textarea name="strip_text"
                          placeholder="Example:
Topic
Exam Version
Practice Only"
                          style="width:100%; height:140px; padding:10px; font-size:14px;"></textarea>

                <br><br>

                <h3>Upload Logo (Optional)</h3>
                <input type="file" name="quiz_logo" accept="image/*">
                <p style="opacity:0.7; font-size:12px">
                    Supported: PNG / JPG / GIF / WEBP
                </p>

                <button type="submit">👀 Preview & Continue</button>
            </form>

            <br>
            <button onclick="location.href='/upload'">📤 Upload File Instead</button>
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>

    </div>
    </body>
    </html>
    """, portal_title=portal_title)



# =========================
# PREVIEW CLEAN TEXT BEFORE PARSE
# =========================
@app.route("/preview_paste", methods=["POST"])
def preview_paste():
    cleanup_temp_logos()   # 🧹 auto-clean old temp logos
    
    quiz_text = request.form.get("quiz_text", "").strip()

    quiz_title = request.form.get("quiz_title", "Generated Quiz From Paste")
    strip_rules_raw = request.form.get("strip_text", "").strip()

    # =========================
    # TEMPORARY LOGO HANDLING
    # =========================
    logo_file = request.files.get("quiz_logo")
    temp_logo_name = None

    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            temp_logo_name = f"temp_{int(time.time())}{ext}"
            logo_file.save(os.path.join(LOGO_FOLDER, temp_logo_name))

    if not quiz_text:
        return "No text provided.", 400

    # Start with raw text
    clean_text = quiz_text

    # Normalize ALL newline styles (Windows, Linux, literal \n)
    clean_text = (
        clean_text
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


       # -------- APPLY STRIP RULES --------
    strip_rules = []
    if strip_rules_raw:
        strip_rules = [r.strip() for r in strip_rules_raw.splitlines() if r.strip()]

    cfg = load_portal_config()
    regex_mode = cfg.get("enable_regex_strip", False)

    if strip_rules:
        cleaned_lines = []

        for line in clean_text.splitlines():
            test = line
            remove = False

            for rule in strip_rules:

                # --- REGEX MODE ---
                if regex_mode:
                    try:
                        if re.search(rule, test, re.IGNORECASE):
                            remove = True
                            break
                    except re.error:
                        # Bad regex shouldn't crash parsing — ignore invalid patterns
                        pass

                # --- NORMAL MODE ---
                else:
                    if rule.lower() in test.lower():
                        remove = True
                        break

            if not remove:
                cleaned_lines.append(line)

        clean_text = "\n".join(cleaned_lines)

    # -------- CONFIDENCE ANALYSIS (NEW) --------
    conf_summary = conf_details = None
    if get_confidence_setting():
        conf_summary, conf_details = analyze_confidence(clean_text)

    # ---------- RENDER PREVIEW ----------
    return render_template_string("""
    <html>
    <head>
        <title>Preview Before Parsing</title>
        <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">
        
        <h1 class="hero-title">👀 Preview Quiz Before Building</h1>

        <div class="card">
            <h2>Quiz Title:</h2>
            <p><b>{{quiz_title}}</b></p>

            <h2>Original Text</h2>
            <pre style="background:black;padding:10px;border-radius:8px;white-space:pre-wrap;">{{original}}</pre>

            <h2>Text To Be Parsed</h2>
            <pre style="background:#102020;padding:10px;border-radius:8px;white-space:pre-wrap;">{{cleaned}}</pre>

            {% if conf_details %}
            <h2>🧠 Confidence Analysis</h2>
            <p>
                <b>Total blocks:</b> {{conf_summary.total}}<br>
                ✅ High: {{conf_summary.high}} &nbsp;
                ⚠ Medium: {{conf_summary.medium}} &nbsp;
                ❌ Low: {{conf_summary.low}}
            </p>

            <ul>
                {% for item in conf_details %}
                <li style="margin-bottom:8px;">
                    <b>Block {{item.index}} ({{item.confidence|capitalize}})</b><br>
                    <span style="opacity:.85">{{item.title}}</span><br>
                    <span style="opacity:.6; font-size:12px;">{{item.reason}}</span>
                </li>
                {% endfor %}
            </ul>
            {% endif %}

            <p style="opacity:.7">
                If this looks correct, continue. Otherwise, go back and adjust rules.
            </p>

            <form action="/download_cleaned" method="POST" style="display:inline;">
                <textarea name="clean_text" style="display:none;">{{cleaned}}</textarea>
                <button type="submit">📥 Download Cleaned Text</button>
            </form>

            <!-- IMPORTANT: Send CLEANED text forward -->
            <form action="/process_paste" method="POST">
                <input type="hidden" name="quiz_title" value="{{quiz_title}}">
                <textarea name="quiz_text" style="display:none;">{{cleaned}}</textarea>

                {% if temp_logo_name %}
                    <input type="hidden" name="temp_logo_name" value="{{temp_logo_name}}">
                {% endif %}

                <button type="submit">✅ Yes, Build My Quiz</button>
            </form>

            <br>
            <button onclick="history.back()">⬅ Go Back & Edit</button>
            <button onclick="location.href='/'">🏠 Return To Portal</button>
        </div>
    </div>
    </body>
    </html>
    """,
    quiz_title=quiz_title,
    original=quiz_text,
    cleaned=clean_text,
    conf_summary=conf_summary,
    conf_details=conf_details,
    temp_logo_name=temp_logo_name
    )





from flask import send_file
from io import BytesIO

@app.route("/download_cleaned", methods=["GET","POST"])
def download_cleaned():
    cleaned = request.form.get("clean_text", "").strip()

    if not cleaned:
        return "No cleaned text available.", 400

    buf = BytesIO()
    buf.write(cleaned.encode("utf-8"))
    buf.seek(0)

    return send_file(
        buf,
        mimetype="text/plain",
        as_attachment=True,
        download_name="cleaned_quiz_text.txt"
    )




# =========================
# PROCESS PASTED QUIZ
# =========================
@app.route("/process_paste", methods=["POST"])
def process_paste():
    cleanup_temp_logos()   # 🧹 clean abandoned logos again

    quiz_text = request.form.get("quiz_text", "").strip()
    quiz_title = request.form.get("quiz_title", "Generated Quiz From Paste")

    # Checkbox flag (Auto Junk Cleanup) – currently unused unless you add a checkbox
    auto_cleanup = request.form.get("auto_cleanup") == "1"

    # Custom strip rules textarea (not used here anymore – handled in preview)
    strip_rules_raw = request.form.get("strip_text", "").strip()

    if not quiz_text:
        return "No text provided.", 400

    clean_text = quiz_text

    # Normalize ALL newline styles (Windows, Linux, Literal \n)
    clean_text = (
        clean_text
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    # AUTO CLEANUP still present but will only run if you wire a checkbox
    if auto_cleanup:
        cleaned_lines = []
        junk_patterns = [
            "topic",
            "chapter",
            "exam version",
            "objective",
            "learning goal",
            "case study",
            "scenario",
            "explanation",
            "rationale",
            "reference",
            "page",
        ]

        for line in clean_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            low = stripped.lower()
            if any(p in low for p in junk_patterns):
                continue

            cleaned_lines.append(line)

        clean_text = "\n".join(cleaned_lines)

    # SAVE CLEANED TEXT
    path = os.path.join(UPLOAD_FOLDER, "pasted.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # PARSE QUIZ
    quiz_data = parse_questions(path)

    if not quiz_data:
        ts_fail = int(time.time())
        log_filename = f"parse_log_{ts_fail}.txt"
        with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
            f.write("\n".join(PARSE_LOG))

        return render_template_string("""
        <html>
        <head>
            <title>Parse Failed</title>
            <link rel="stylesheet" href="/style.css">
        </head>
        <body>
        <div class="container">
            <h1 class="hero-title">⚠️ Could Not Parse Any Questions</h1>
            <div class="card">
                <p>No valid questions were parsed. Please check the formatting.</p>
                <p>You can download the parser log for troubleshooting:</p>

                <button onclick="location.href='/data/{{log_filename}}'">
                    📥 Download Parse Log
                </button>

                <br><br>
                <button onclick="location.href='/paste'">⬅ Back To Paste Page</button>
                <button onclick="location.href='/'">🏠 Return To Portal</button>
            </div>
        </div>
        </body>
        </html>
        """, log_filename=log_filename), 400

    # SAVE OUTPUTS
    ts = int(time.time())

    # Save parse debug log
    log_filename = f"parse_log_{ts}.txt"
    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

        # =========================
    # HANDLE LOGO (Supports preview temp logo)
    # =========================
    logo_filename = None

    # 1️⃣ If a logo was uploaded here directly (upload flow)
    logo_file = request.files.get("quiz_logo")
    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            logo_filename = f"logo_{ts}{ext}"
            logo_file.save(os.path.join(LOGO_FOLDER, logo_filename))

    # 2️⃣ If coming from PREVIEW and a temp logo exists
    else:
        temp_logo_name = request.form.get("temp_logo_name")
        if temp_logo_name:
            old_path = os.path.join(LOGO_FOLDER, temp_logo_name)
            if os.path.exists(old_path):
                ext = os.path.splitext(temp_logo_name)[1].lower()
                logo_filename = f"logo_{ts}{ext}"
                new_path = os.path.join(LOGO_FOLDER, logo_filename)
                os.rename(old_path, new_path)

    # =========================
    # SAVE JSON + HTML quiz
    # =========================
    json_name = f"quiz_{ts}.json"
    html_name = f"quiz_{ts}.html"

    with open(os.path.join(DATA_FOLDER, json_name), "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=4)

    build_quiz_html(
        html_name,
        json_name,
        os.path.join(QUIZ_FOLDER, html_name),
        get_portal_title(),
        quiz_title,
        logo_filename
    )


    add_quiz_to_registry(html_name, quiz_title, logo_filename)

    return render_template_string("""
    <html>
    <head>
        <title>Quiz Built</title>
        <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            ✅ Quiz Successfully Built
        </h1>

        <div class="card">
            <p><b>{{quiz_title}}</b> has been created in your library.</p>

            <button onclick="location.href='/quizzes/{{html_name}}'">
                ▶ Open Quiz
            </button>

            <button onclick="location.href='/library'">
                📚 Return To Quiz Library
            </button>

            <button onclick="location.href='/data/{{log_filename}}'">
                📥 Download Parse Log
            </button>

            <br><br>
            <button onclick="location.href='/'">
                🏠 Return To Portal</button>
        </div>

    </div>
    </body>
    </html>
    """, quiz_title=quiz_title, html_name=html_name, log_filename=log_filename)







# =========================
# PROCESS UPLOAD
# =========================
@app.route("/process", methods=["POST"])
def process_file():
    file = request.files["file"]

    if not file.filename.lower().endswith(".txt"):
        return "Only .txt files are supported.", 400

    quiz_title = request.form.get("quiz_title", "Generated Quiz")

    if not file:
        return "No file uploaded", 400

    path = os.path.join(UPLOAD_FOLDER, "latest.txt")
    file.save(path)

    logo_file = request.files.get("quiz_logo")
    logo_filename = None

    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            ts = int(time.time())
            logo_filename = f"logo_{ts}{ext}"
            logo_file.save(os.path.join(LOGO_FOLDER, logo_filename))

    quiz_data = parse_questions(path)

    if not quiz_data:
        return "Could not parse any questions. Check formatting.", 400

    ts = int(time.time())
    json_name = f"quiz_{ts}.json"
    html_name = f"quiz_{ts}.html"

    with open(os.path.join(DATA_FOLDER, json_name), "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=4)

    build_quiz_html(
        html_name,
        json_name,
        os.path.join(QUIZ_FOLDER, html_name),
        get_portal_title(),
        quiz_title,
        logo_filename
    )

    add_quiz_to_registry(html_name, quiz_title, logo_filename)

    return redirect("/library")


# =========================
# SETTINGS PAGE
# =========================
@app.route("/settings")
def settings_page():
    cfg = load_portal_config()

    return render_template_string("""
    <html>
    <head>
    <title>Portal Settings</title>
    <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            ⚙️ Portal Configuration
        </h1>

        <div class="card">

            <form action="/save_settings" method="POST">

                <h3>Training Portal Title</h3>
                <input type="text"
                       name="portal_title"
                       value="{{cfg.title}}"
                       required style="width:100%; padding:6px">

                <br><br>

<h3>Confidence Analysis</h3>
<p style="opacity:.7">
    Controls whether the 🧠 Confidence Analysis panel appears on quiz preview.
</p>

<label style="display:flex; gap:10px; align-items:center;">
    <input type="checkbox" name="show_confidence"
           value="1"
           {% if cfg.show_confidence %}checked{% endif %}>
    Enable Confidence Analysis on Preview
</label>

<br><br>

<h3>Regex Strip Mode</h3>
<p style="opacity:.7">
    If enabled, the Strip Text box in Paste Mode will treat entries as REGEX patterns
    instead of simple text matches.
</p>

<label style="display:flex; gap:10px; align-items:center;">
    <input type="checkbox" name="enable_regex_strip"
           value="1"
           {% if cfg.enable_regex_strip %}checked{% endif %}>
    Enable Regex Strip Rules
</label>

              

                <button type="submit">💾 Save Settings</button>
            </form>

            <br>
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>

    </div>
    </body>
    </html>
    """, cfg=cfg)

@app.route("/save_settings", methods=["POST"])
def save_settings():
    title = request.form.get("portal_title", "Training & Practice Center")
    show_conf = request.form.get("show_confidence") == "1"
    enable_regex = request.form.get("enable_regex_strip") == "1"

    save_portal_config(title, show_conf, enable_regex)

    return redirect("/settings")




# =========================
# CONFIDENCE ANALYSIS ENGINE
# =========================
def analyze_confidence(text):
    import re

    blocks = re.split(
        r"(?=^\s*(?:Question\s*#?\s*\d+|\d+\s*[.) ]))",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    details = []
    total = len(blocks)
    high = medium = low = 0

    for block in blocks:
        b = block.strip()
        if not b:
            continue

        score = 0
        reasons = []

        # --- Choices Check ---
        choices = re.findall(r"^[A-F][\.\)]", b, flags=re.MULTILINE)
        if len(choices) >= 2:
            score += 40
            reasons.append("Detected multiple answer choices")
        else:
            reasons.append("Missing or too few answer choices")

        # --- Has Correct Answer ---
        if re.search(r"correct answer|suggested answer", b, re.IGNORECASE):
            score += 40
            reasons.append("Detected an answer key line")
        else:
            reasons.append("No clear answer key line found")

        # --- Length / Structure ---
        if len(b) > 120:
            score += 20
            reasons.append("Looks like full valid question text")
        else:
            reasons.append("Question block looks short/incomplete")

        # ---------- Confidence Bucket ----------
        if score >= 80:
            level = "HIGH"
            high += 1
        elif score >= 40:
            level = "MEDIUM"
            medium += 1
        else:
            level = "LOW"
            low += 1

        details.append({
            "confidence": level,
            "score": score,
            "preview": b[:400],
            "reasons": reasons
        })

    summary = {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low
    }

    return summary, details




# =========================
# ROBUST PARSER + LOGGING
# =========================
DEBUG_PARSE = True
PARSE_LOG = []


def dbg(*msg):
    text = " ".join(str(m) for m in msg)
    if DEBUG_PARSE:
        print("[PARSE]", text)
    PARSE_LOG.append(text)


def parse_questions(filepath):
    import re

    global PARSE_LOG
    PARSE_LOG.clear()
    dbg("=== NEW PARSE SESSION STARTED ===")

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    # Normalize newlines
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Split into question blocks
    blocks = re.split(
        r"(?=^\s*(?:Question\s*#?\s*\d+|\d+\s*[.) ]))",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    dbg("Total detected blocks:", len(blocks))

    questions = []
    number = 1

    # ===================================
    # MAIN PARSE LOOP
    # ===================================
    for block in blocks:
        original_block = block
        block = block.strip()
        if not block:
            dbg("Skipped: empty block")
            continue

        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) < 2:
            dbg("Skipped: too few lines:", repr(lines))
            continue

        dbg(f"\n--- Parsing Question Candidate #{number} ---")
        dbg(lines[0])

        q_lines = []
        choices = []
        correct = None
        choices_started = False

        # ================================
        # PARSE EACH LINE
        # ================================
        for line in lines:
            lower = line.lower()

            # -------- Detect Choices --------
            mchoice = re.match(r"^\s*([A-Da-d])[\.\)]\s+(.*)", line)
            if mchoice:
                label = mchoice.group(1).upper()
                text_choice = mchoice.group(2).strip()
                dbg(f"Choice detected: {label} → {text_choice}")
                choices_started = True
                choices.append(text_choice)
                continue

            # -------- Detect Correct Answer --------
            if "correct answer" in lower or "suggested answer" in lower:

                dbg("Found answer line:", line)

                m = re.search(r"[:\-]\s*([A-Za-z]+)", line)
                if m:
                    ans = re.sub(r'[^A-Za-z]', '', m.group(1)).upper()
                    if ans:
                        correct = list(dict.fromkeys(list(ans)))
                        dbg("Parsed correct letters:", correct)
                    else:
                        dbg("!! Failed to parse answer text")
                else:
                    dbg("!! Could not read answer format")
                continue

            # -------- Question Text --------
            if not choices_started:
                q_lines.append(line)

        # ================================
        # VALIDATION
        # ================================
        if not correct:
            dbg("!! Skipped: NO correct answer found")
            dbg(original_block[:200])
            continue

        if len(choices) < 2:
            dbg("!! Skipped: Not enough choices:", choices)
            continue

        question_text = " ".join(q_lines)
        dbg("Final Question Built:", question_text[:150])

        questions.append({
            "number": number,
            "question": question_text,
            "choices": choices,
            "correct": correct
        })

        dbg("✓ Question Accepted\n")
        number += 1

    dbg("\n==== PARSE COMPLETE ====")
    dbg("Total questions parsed:", len(questions))

    return questions


# =========================
# CONFIDENCE ANALYZER (for preview only)
# =========================
def analyze_confidence(clean_text):
    """
    Heuristic pre-check of the raw text BEFORE parsing.
    Used only for preview so the user can see if their input
    looks parse-friendly.
    """
    import re

    blocks = re.split(
        r"(?=^\s*(?:Question\s*#?\s*\d+|\d+\s*[.) ]))",
        clean_text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    details = []
    high = med = low = 0
    idx = 0

    for raw in blocks:
        block = raw.strip()
        if not block:
            continue

        idx += 1
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        txt = " ".join(lines)

        # Basic signals
        has_choice = any(re.match(r"^[A-Da-d][\.\)]\s+", l) for l in lines)
        has_answer_line = any(
            ("correct answer" in l.lower()) or ("suggested answer" in l.lower())
            for l in lines
        )
        num_choices = sum(
            1 for l in lines if re.match(r"^[A-Da-d][\.\)]\s+", l)
        )

        score = 0
        reason = []

        if has_choice:
            score += 1
            reason.append("Found A–D answer choices")
        else:
            reason.append("No A–D answer choices found")

        if has_answer_line:
            score += 1
            reason.append("Found 'Correct/Suggested Answer' line")
        else:
            reason.append("No explicit correct-answer line found")

        if 2 <= num_choices <= 6:
            score += 1
            reason.append(f"{num_choices} choices detected")
        else:
            reason.append(f"{num_choices} choices detected (unusual count)")

        if score == 3:
            conf = "high"
            high += 1
        elif score == 2:
            conf = "medium"
            med += 1
        else:
            conf = "low"
            low += 1

        title = lines[0][:80] if lines else "[empty]"

        details.append({
            "index": idx,
            "title": title,
            "confidence": conf,
            "reason": "; ".join(reason),
        })

    summary = {
        "high": high,
        "medium": med,
        "low": low,
        "total": len(details),
    }
    return summary, details


# =========================
# QUIZ HTML BUILDER
# =========================
def build_quiz_html(name, jsonfile, outpath, portal_title, quiz_title, logo_filename):
    # Optional logo for mode banner (left/right)
    if logo_filename:
        mode_logo = f'<img src="/static/logos/{logo_filename}" class="mode-badge">'
    else:
        mode_logo = ""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{quiz_title}</title>
<link rel="stylesheet" href="/style.css">
</head>

<body>

<!-- 🔹 Overlay shown when exam is paused -->
<div id="pauseOverlay" class="pause-overlay">
    <div class="pause-overlay-content">
        <h2>Exam Paused</h2>
        <p>Your time is frozen. Click Resume to continue.</p>
        <button onclick="resumeExam()">Resume</button>
    </div>
</div>

<!-- 🔹 Everything that should blur goes inside this wrapper -->
<div id="quizWrapper" class="blur-wrapper">
    <div class="container">

        <!-- Readable Centered Banner -->
        <h1 class="hero-title">
            {portal_title}<br>
            <span style="font-size:20px;opacity:.85">{quiz_title}</span>
        </h1>

        <!-- Mode Select -->
        <div id="modeSelect" class="card">
            <div class="mode-banner">
                {mode_logo}
                <div class="mode-center">
                    <h2>Select Mode</h2>
                    <button onclick="startQuiz(false)">Study Mode</button>
                    <button onclick="startQuiz(true)">Exam Mode</button>
                </div>
                {mode_logo}
            </div>
        </div>

        <!-- Quiz Area -->
        <div id="quiz" class="hidden">

            <!-- Progress Bar -->
            <div id="progressBarOuter">
                <div id="progressBarInner"></div>
            </div>

            <!-- Exam Timer -->
            <div id="timer" class="hidden timerBox">
                <b>Time Remaining:</b>
                <span id="timeDisplay">--:--</span>

                <button id="pauseBtn" onclick="pauseExam()">Pause</button>
                
            </div>

            <div id="qHeader"></div>
            <div id="qText"></div>
            <div id="choices"></div>

            <div class="controls">
                <button onclick="prev()">Prev</button>
                <button onclick="next()">Next</button>
                <button onclick="submitQuiz()">Submit Exam</button>
            </div>
        </div>

        <div id="result" class="hidden"></div>

        <br>
        <button onclick="location.href='/'">🏠 Return To Portal</button>
        <button onclick="location.href='/library'">📚 Return To Quiz Library</button>

    </div>
</div>

<script>
  /* This tells script.js which JSON file to load for this quiz */
  const QUIZ_FILE = "/data/{jsonfile}";
</script>

<script src="/script.js"></script>
</body>
</html>
"""
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)




# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
