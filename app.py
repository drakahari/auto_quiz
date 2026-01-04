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

            <form action="/process_paste" method="POST" enctype="multipart/form-data">

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

                <h3>Upload Logo (Optional)</h3>
                <input type="file" name="quiz_logo" accept="image/*">
                <p style="opacity:0.7; font-size:12px">
                    Supported: PNG / JPG / GIF / WEBP
                </p>

                <button type="submit">Convert & Build Quiz</button>
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
# PROCESS PASTED QUIZ
# =========================
@app.route("/process_paste", methods=["POST"])
def process_paste():
    quiz_text = request.form.get("quiz_text", "").strip()
    quiz_title = request.form.get("quiz_title", "Generated Quiz From Paste")

    if not quiz_text:
        return "No text provided.", 400

    # Save pasted text to temp file so parser can reuse logic
    path = os.path.join(UPLOAD_FOLDER, "pasted.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(quiz_text)

    # This will also reset + populate PARSE_LOG because of parse_questions()
    quiz_data = parse_questions(path)

    if not quiz_data:
        # Even in failure cases, PARSE_LOG is useful
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

    # Common timestamp for files
    ts = int(time.time())

    # =========================
    # SAVE PARSE LOG 🎯
    # =========================
    
    log_filename = f"parse_log_{ts}.txt"
    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

    # =========================
    # HANDLE LOGO (OPTIONAL)
    # =========================
    logo_file = request.files.get("quiz_logo")
    logo_filename = None

    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            logo_filename = f"logo_{ts}{ext}"
            logo_file.save(os.path.join(LOGO_FOLDER, logo_filename))

    # =========================
    # SAVE JSON + BUILD QUIZ
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

    # =========================
    # SUCCESS PAGE 🎉
    # =========================
    portal_title = get_portal_title()

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
                🏠 Return To Portal
            </button>
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
# ROBUST PARSER + LOGGING
# =========================
DEBUG_PARSE = True     # Turn ON console debugging
PARSE_LOG = []         # Stores debug log for download


def dbg(*msg):
    """
    Debug helper. Prints to console (if DEBUG_PARSE)
    AND stores a full debug transcript in PARSE_LOG.
    """
    text = " ".join(str(m) for m in msg)

    # Console logging (optional)
    if DEBUG_PARSE:
        print("[PARSE]", text)

    # Always capture log in memory
    PARSE_LOG.append(text)


def parse_questions(filepath):
    import re

    # =========================
    # RESET LOG PER SESSION 🚀
    # =========================
    global PARSE_LOG
    PARSE_LOG.clear()
    dbg("=== NEW PARSE SESSION STARTED ===")

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    blocks = re.split(
        r"(?=^\s*(?:Question\s*#?\s*\d+|\d+\s*[.) ]))",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    dbg("Total detected blocks:", len(blocks))

    questions = []
    number = 1

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
        dbg(lines[0][:120] + ("..." if len(lines[0]) > 120 else ""))

        q_lines = []
        choices = []
        correct = None
        choices_started = False

        for line in lines:
            lower = line.lower().replace(" ", "")

            # ===== ANSWER CHOICES =====
            mchoice = re.match(r"^\s*([A-Za-z])[\.\)]?\s+(.*)", line, re.IGNORECASE)
            if mchoice:
                label = mchoice.group(1).upper()
                text_choice = mchoice.group(2).strip()
                dbg(f"Choice detected: {label} → {text_choice}")
                choices_started = True
                choices.append(text_choice)
                continue

            # ===== CORRECT / SUGGESTED =====
            if lower.startswith("suggestedanswer") or lower.startswith("correctanswer"):
                dbg("Found answer line:", line)

                m = re.search(r"[:\-]\s*([A-Za-z]+)", line)
                if not m:
                    m = re.search(r"\s+([A-Za-z]+)\s*$", line)

                if m:
                    ans = m.group(1)
                    parsed = re.sub(r'[^A-Za-z]', '', ans).upper()
                    if parsed:
                        correct = list(dict.fromkeys(list(parsed)))
                        dbg("Parsed answer letters:", correct)
                    else:
                        dbg("!! Could not extract letters from:", ans)
                else:
                    dbg("!! No recognizable answer format found")

                continue

            # Part of question text
            if not choices_started:
                q_lines.append(line)

        # ===== FINAL VALIDATION =====
        if not correct:
            dbg("!! Skipped: NO correct answer found")
            dbg(original_block[:200])
            continue

        if len(choices) < 2:
            dbg("!! Skipped: Not enough choices:", choices)
            continue

        question_text = " ".join(q_lines)
        dbg("Final Question Built:", question_text[:120])

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
