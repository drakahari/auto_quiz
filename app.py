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
# PORTAL TITLE
# =========================
def get_portal_title():
    if os.path.exists(PORTAL_CONFIG):
        try:
            with open(PORTAL_CONFIG, "r") as f:
                return json.load(f).get("title", "Training & Practice Center")
        except:
            pass
    return "Training & Practice Center"


def save_portal_title(title):
    with open(PORTAL_CONFIG, "w") as f:
        json.dump({"title": title}, f, indent=4)


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

# =========================
# HOME PAGE (DYNAMIC)
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


# Catch-all LAST
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
# LIBRARY
# =========================
@app.route("/library")
def quiz_library():
    quizzes = sorted(load_registry(), key=lambda x: x["timestamp"], reverse=True)
    portal_title = get_portal_title()

    return render_template_string("""
    <html>
    <head>
        <title>Quiz Library</title>
        <link rel="stylesheet" href="/style.css">
    </head>

    <body>
    <div class="container">

        <h1 class="hero-title">
            {{portal_title}}<br>
            <span style="font-size:22px;opacity:.85">📚 Quiz Library</span>
        </h1>

        <div class="card">

            {% if quizzes %}
                <h2>Available Quizzes</h2>

                {% for q in quizzes %}
                <div class="quiz-card"
                     style="padding:12px; margin:10px; background:rgba(0,0,0,.6); border-radius:8px;">

                    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                        
                        <div>
                            <h3 style="margin:0;">
                                {{q['title']}}
                            </h3>
                            <small>{{q['html']}}</small>
                        </div>

                        {% if q.get('logo') %}
                        <img src="/static/logos/{{q['logo']}}"
                             style="max-height:70px; width:auto;">
                        {% endif %}
                    </div>

                    <div style="margin-top:10px; display:flex; gap:10px;">

                        <button
                            onclick="location.href='/quizzes/{{q['html']}}'"
                            style="
                                background:#1e9bff;
                                color:white;
                                border:none;
                                padding:6px 12px;
                                border-radius:6px;
                                cursor:pointer;
                                font-size:14px;">
                            ▶️ Open Quiz
                        </button>

                        <form method="POST"
                              action="/delete_quiz/{{q['html']}}"
                              onsubmit="return confirm('Delete this quiz permanently?');">

                            <button type="submit" style="
                                background:#7a0000;
                                color:white;
                                border:none;
                                padding:4px 8px;
                                font-size:12px;
                                border-radius:6px;
                                opacity:.8;
                                cursor:pointer;">
                                🗑 Delete
                            </button>

                        </form>
                    </div>

                </div>
                {% endfor %}

            {% else %}
                <p>No quizzes created yet. Upload one 😊</p>
            {% endif %}

            <br>
            <button onclick="location.href='/upload'">📤 Upload New Quiz</button>
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>

    </div>
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
            📤 Upload Quiz
        </h1>

        <div class="card">

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

                <button type="submit">Upload & Build Quiz</button>
            </form>

            <br>
            <button onclick="location.href='/'">⬅ Back To Portal</button>
        </div>
    </div>
    </body>
    </html>
    """)


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

    with open(os.path.join(DATA_FOLDER, json_name), "w") as f:
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
    portal_title = get_portal_title()

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
                       value="{{portal_title}}"
                       required style="width:100%; padding:6px">

                <br><br>

                <button type="submit">💾 Save Settings</button>
            </form>

            <br>
            <button onclick="location.href='/'">⬅ Back To Portal</button>

        </div>

    </div>
    </body>
    </html>
    """, portal_title=portal_title)


@app.route("/save_settings", methods=["POST"])
def save_settings():
    title = request.form.get("portal_title", "Training & Practice Center")
    save_portal_title(title)
    return redirect("/")


# =========================
# ROBUST PARSER
# =========================
def parse_questions(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    blocks = re.split(
        r"(?=(?:Question\s*#\d+)|(?:^\d+\.) )",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    questions = []
    number = 1

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = [l.strip() for l in block.split("\n") if l.strip()]

        if len(lines) < 3:
            continue

        q_lines = []
        choices = []
        correct = None
        choices_started = False

        for line in lines:

            mchoice = re.match(r"([A-D])[\.\)]\s*(.+)", line, flags=re.IGNORECASE)
            if mchoice:
                choices_started = True
                choices.append(mchoice.group(2).strip())
                continue

            lower = line.lower()

            if lower.startswith("correct answer") or lower.startswith("suggested answer"):
                m = re.search(r"[:\-]\s*[\(\[]?([A-D])[\)\]]?", line, re.IGNORECASE)
                if m:
                    correct = m.group(1).upper()
                continue

            if not choices_started:
                q_lines.append(line)

        if not correct or len(choices) < 2:
            continue

        question_text = " ".join(q_lines)

        questions.append({
            "number": number,
            "question": question_text,
            "choices": choices,
            "correct": [correct]
        })

        number += 1

    return questions


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

            <button onclick="document.body.classList.toggle('high-contrast')">
                🌓 Toggle High Contrast
            </button>

            <!-- Exam Timer -->
            <div id="timer" class="hidden timerBox">
                <b>Time Remaining:</b>
                <span id="timeDisplay">--:--</span>

                <button id="pauseBtn" onclick="pauseExam()">Pause</button>
                <button id="resumeBtn" class="hidden" onclick="resumeExam()">Resume</button>
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
