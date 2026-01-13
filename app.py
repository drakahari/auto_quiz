from flask import Flask, send_from_directory, request, redirect, render_template_string, jsonify, Response
import os, re, json, time, sqlite3, sys
from werkzeug.utils import secure_filename

# =========================
# PYINSTALLER PATH HELPER
# =========================
def resource_path(relative_path: str) -> str:
    """
    Resolve paths correctly in dev and when bundled by PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# =========================
# APP DATA DIRECTORY
# =========================
def get_app_data_dir(app_name: str = "DLMS") -> str:
    override = os.getenv("QUIZAPP_DATA_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override

    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")

    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path

APP_NAME = "DLMS"
APP_DATA_DIR = get_app_data_dir(APP_NAME)

# =========================
# STATIC ROOT SELECTION
# =========================
def get_static_root():
    if getattr(sys, "frozen", False):
        # PyInstaller bundle: static assets live inside the bundle
        return os.path.join(sys._MEIPASS, "static")
    else:
        # Dev mode: static assets live next to app.py
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


STATIC_ROOT = get_static_root()

# =========================
# FLASK APP
# =========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

print("[DEBUG] Flask static folder =", app.static_folder)
print("[BUILD CHECK] APP_DATA_DIR =", APP_DATA_DIR)








import sys

DEBUG_LOGS = False

def dprint(*args, **kwargs):
    if DEBUG_LOGS:
        print(*args, **kwargs)

#dprint("DEBUG TEST — YOU SHOULD NOT SEE THIS")
print("[DEBUG] Flask static folder =", app.static_folder)




def resource_path(relative_path: str) -> str:
    """
    Resolve paths correctly in dev and when bundled by PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)


def get_app_data_dir(app_name: str = "DLMS") -> str:
    """
    Return a user-writable directory for runtime data.
    """
    override = os.getenv("QUIZAPP_DATA_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override

    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")

    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path




# =========================
# PATH SETUP
# =========================
BASE_DIR = resource_path("")
IS_BUNDLED = hasattr(sys, "_MEIPASS")

APP_NAME = "DLMS"
APP_DATA_DIR = get_app_data_dir(APP_NAME)

print("[BUILD CHECK] APP_DATA_DIR =", APP_DATA_DIR)



UPLOAD_FOLDER = os.path.join(APP_DATA_DIR, "uploads")
DATA_FOLDER = os.path.join(APP_DATA_DIR, "data")
QUIZ_FOLDER = os.path.join(APP_DATA_DIR, "quizzes")
CONFIG_FOLDER = os.path.join(APP_DATA_DIR, "config")

# App-data logos (used for temp storage / preview)
LOGO_FOLDER = os.path.join(APP_DATA_DIR, "static", "logos")

# Flask-served logos (what the browser loads)
STATIC_LOGO_FOLDER = os.path.join(app.root_path, "static", "logos")

BACKGROUND_FOLDER = os.path.join(APP_DATA_DIR, "static", "bg")

for d in [
    UPLOAD_FOLDER,
    DATA_FOLDER,
    QUIZ_FOLDER,
    CONFIG_FOLDER,
    BACKGROUND_FOLDER,
    LOGO_FOLDER,
    STATIC_LOGO_FOLDER,
]:
    os.makedirs(d, exist_ok=True)



PORTAL_CONFIG = os.path.join(CONFIG_FOLDER, "portal.json")
QUIZ_REGISTRY = os.path.join(CONFIG_FOLDER, "quizzes.json")
DB_PATH = os.path.join(APP_DATA_DIR, "results.db")

REQUIRED_TABLES = {
    "quizzes",
    "questions",
    "choices",
    "attempts",
    "attempt_answers",
    "missed_questions",
    "schema_meta",
}



def ensure_db_initialized():
    """
    Ensure the SQLite database exists and has all required tables.
    Runs exactly once at import time.
    """
    dprint(f"[DB] ensure_db_initialized using DB_PATH = {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch all existing table names
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
    """)
    existing_tables = {row[0] for row in cur.fetchall()}

    # Determine which required tables are missing
    missing_tables = REQUIRED_TABLES - existing_tables

    if missing_tables:
        dprint(f"[DB] Missing tables detected: {missing_tables}")

        init_sql_path = resource_path(os.path.join("data", "init.sql"))
        dprint(f"[DB] init.sql path = {init_sql_path}")

        with open(init_sql_path, "r", encoding="utf-8") as f:
            sql = f.read()

        conn.executescript(sql)
        conn.commit()

        print("[DB] Database schema initialized / updated")

    conn.close()


# ✅ INITIALIZE DATABASE ONCE, AT IMPORT TIME
ensure_db_initialized()

# =========================
# SERVE RUNTIME LOGOS
# =========================
#@app.route("/static/logos/<path:filename>")
#def serve_runtime_logos(filename):
    #return send_from_directory(LOGO_FOLDER, filename)








@app.route("/config/portal.json")
def serve_portal_config():
    """
    Serve the portal configuration as JSON.
    This is the single source of truth for UI settings
    (title, background image, feature toggles).
    """
    dprint("\n[PORTAL CONFIG] ===== SERVING /config/portal.json =====")
    dprint("[PORTAL CONFIG] Reading from:", PORTAL_CONFIG)

    try:
        with open(PORTAL_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        dprint("[PORTAL CONFIG] Loaded config:", cfg)
    except Exception as e:
        print("[PORTAL CONFIG][ERROR] Failed to load config:", e)
        cfg = {}

    dprint("[PORTAL CONFIG] ===== END SERVE =====\n")
    return jsonify(cfg)




@app.route("/dynamic.css")
def dynamic_css():
    cfg = load_portal_config()
    bg = cfg.get("background_image", "/static/fiber.jpg")

    return f"""
:root {{
  --portal-bg: url('{bg}');
}}
""", 200, {"Content-Type": "text/css"}





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

cleanup_temp_logos()


# =========================
# PORTAL CONFIG MANAGEMENT
# =========================
def load_portal_config():
    default = {
        "title": "Training & Practice Center",
        "show_confidence": True,
        "enable_regex_replace": False
    }

    if not os.path.exists(PORTAL_CONFIG):
        return default

    try:
        with open(PORTAL_CONFIG, "r") as f:
            data = json.load(f)
            return {
                "title": data.get("title", default["title"]),
                "show_confidence": data.get("show_confidence", True),
                "enable_regex_replace": data.get("enable_regex_replace", False)
            }
    except:
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


def add_quiz_to_registry(html, title, logo):
    registry = load_registry()

    # 🔁 remove existing quiz with same title
    registry = [
        q for q in registry
        if q.get("title") != title
    ]

    registry.append({
        "html": html,
        "title": title,
        "logo": logo,
        "timestamp": int(time.time())
    })

    save_registry(registry)



# =========================
# ROOT + STATIC (ORDER MATTERS)
# =========================

@app.route("/")
def home():
    portal_title = get_portal_title()

    index_path = os.path.join(app.static_folder, "index.html")

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    return render_template_string(html, portal_title=portal_title)




@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(DATA_FOLDER, filename)


@app.route("/quizzes/<path:filename>")
def serve_quiz(filename):
    return send_from_directory(QUIZ_FOLDER, filename)


#@app.route("/<path:path>")
#def static_proxy(path):
    #return send_from_directory(".", path)


# =========================
# DELETE QUIZ (CANONICAL)
# =========================
@app.route("/delete_quiz/<int:quiz_id>", methods=["POST"])
def delete_quiz(quiz_id):
    conn = get_db()

    # 🔒 Ensure FK cascades are enforced for this connection
    conn.execute("PRAGMA foreign_keys = ON")

    # ----------------------------------
    # Look up quiz metadata BEFORE delete
    # ----------------------------------
    row = conn.execute(
        "SELECT title, source_file FROM quizzes WHERE id = ?",
        (quiz_id,)
    ).fetchone()

    if not row:
        conn.close()
        return redirect("/library")

    source_file = row["source_file"]

    # ----------------------------------
    # DELETE FROM DATABASE (AUTHORITATIVE)
    # ----------------------------------
    conn.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    conn.commit()
    conn.close()

    # ----------------------------------
    # CLEAN UP REGISTRY + FILES
    # ----------------------------------
    registry = load_registry()
    updated = []

    json_file_to_delete = None
    logo_to_delete = None
    html_file_to_delete = None

    for q in registry:
        if q.get("html") == source_file:
            html_file_to_delete = q.get("html")
            try:
                json_file_to_delete = q.get("html", "").replace(".html", ".json")
            except Exception:
                pass
            logo_to_delete = q.get("logo")
            continue
        updated.append(q)

    save_registry(updated)

    # ----------------------------------
    # DELETE FILES (BEST EFFORT)
    # ----------------------------------
    if html_file_to_delete:
        hp = os.path.join(QUIZ_FOLDER, html_file_to_delete)
        if os.path.exists(hp):
            os.remove(hp)

    if json_file_to_delete:
        jp = os.path.join(DATA_FOLDER, json_file_to_delete)
        if os.path.exists(jp):
            os.remove(jp)

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
# QUIZ DB SAVE HELPER (UPLOAD + PASTE)
# =========================
def save_quiz_to_db(quiz_title, source_file, quiz_data, logo_filename=None):
    conn = get_db()
    cur = conn.cursor()

    # Replace existing quiz with same source_file
    cur.execute(
        "DELETE FROM quizzes WHERE source_file = ?",
        (source_file,)
    )

    # Insert quiz
    cur.execute(
        """
        INSERT INTO quizzes (title, source_file)
        VALUES (?, ?)
        """,
        (quiz_title, source_file),
    )
    quiz_id = cur.lastrowid

    # Insert questions + choices
    for q in quiz_data:
        question_number = q.get("number")
        question_text = q.get("question") or q.get("text") or ""
        q_choices = q.get("choices", [])

        cur.execute(
            """
            INSERT INTO questions (
                quiz_id,
                question_number,
                question_text
            )
            VALUES (?, ?, ?)
            """,
            (quiz_id, question_number, question_text),
        )
        question_id = cur.lastrowid

        for c in q_choices:
            cur.execute(
                """
                INSERT INTO choices (question_id, label, text, is_correct)
                VALUES (?, ?, ?, ?)
                """,
                (
                    question_id,
                    c.get("label"),
                    c.get("text"),
                    1 if c.get("is_correct") else 0,
                ),
            )

    conn.commit()
    conn.close()




# =========================
# LIBRARY (WITH DRAG + DROP!)
# =========================
@app.route("/library")
def quiz_library():
    registry = load_registry()   # ← MUST come first

    dprint("[DEBUG] Using registry file:", QUIZ_REGISTRY)
    dprint("[DEBUG] Registry contents:", registry)

    # =========================
    # DEBUG: Verify logo files exist on disk
    # =========================
    for q in registry:
        logo = q.get("logo")
        if logo:
            path = os.path.join(LOGO_FOLDER, logo)
            dprint("[DEBUG] Logo check:", logo, "exists =", os.path.exists(path), "path =", path)

    portal_title = get_portal_title()


    conn = get_db()
    conn.execute("PRAGMA foreign_keys = ON")

    quizzes = []

    for q in registry:
        merged = dict(q)

        # Try to resolve DB quiz ID
        row = conn.execute(
            """
            SELECT id FROM quizzes
            WHERE source_file = ?
               OR title = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (q.get("html"), q.get("title"))
        ).fetchone()

        if not row:
            # No DB row → skip delete capability entirely
            # (quiz still renders, but delete is harmless)
            continue

        merged["id"] = row["id"]
        quizzes.append(merged)

    conn.close()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Quiz Library</title>
    <link rel="stylesheet" href="/static/style.css">

    <!-- Drag + Drop Library -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>

    <!-- Background Loader -->
    <script>
    fetch("/config/portal.json")
      .then(r => r.json())
      .then(cfg => {
          if (cfg.background_image) {
              document.documentElement.style.setProperty(
                  "--portal-bg",
                  `url(${cfg.background_image})`
              );
          }
      });
    </script>
</head>

<body>

<div class="container">

    <h1 class="hero-title">
        {{ portal_title }}<br>
        <span style="font-size:22px;opacity:.85">📚 Quiz Library</span>
    </h1>

    <div class="card">

        {% if quizzes %}
            <h2>Drag to Reorder</h2>

            <div id="quizList">
            {% for q in quizzes %}
                <div class="quiz-card"
                     data-id="{{ q['html'] }}"
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
                            {{ q['title'] }}
                        </h3>

                        <div style="margin-top:10px;">
                            <button onclick="location.href='/quizzes/{{ q['html'] }}'"
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

                        {% if q['logo'] %}
                        <img src="/static/logos/{{ q['logo'] }}"
                             style="max-height:90px; width:auto;">
                        {% else %}
                        <div style="height:90px;"></div>
                        {% endif %}

                        <form method="POST"
                              action="/delete_quiz/{{ q['id'] }}"
                              onsubmit="return confirm('Delete this quiz permanently?');"
                              style="margin-top:12px; width:100%; text-align:center;">

                            <button type="submit"
                                    style="
                                        width:100%;
                                        background:#7a0000;
                                        color:white;
                                        border:none;
                                        padding:7px 0;
                                        font-size:13px;
                                        border-radius:6px;
                                        cursor:pointer;
                                    ">
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

if (list) {
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
}
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

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Upload Quiz File</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

    <script>
fetch("/config/portal.json")
  .then(r => r.json())
  .then(cfg => {
      if (cfg.background_image) {
          document.documentElement.style.setProperty(
              "--portal-bg",
              `url(${cfg.background_image})`
          );
      }
  });
</script>


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
    """, portal_title=portal_title)




# =========================
# PASTE QUIZ PAGE
# =========================
@app.route("/paste")
def paste_page():
    portal_title = get_portal_title()
    cfg = load_portal_config()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Paste Quiz Questions</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

    <script>
    fetch("/config/portal.json")
    .then(r => r.json())
    .then(cfg => {
        if (cfg.background_image) {
            document.documentElement.style.setProperty(
                "--portal-bg",
                `url(${cfg.background_image})`
            );
        }
    });
    </script>


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

                <p style="opacity:.85; font-size:13px">
                    <strong>Important:</strong> Each question <u>must include</u> a final answer line in one of the following formats
                    for parsing to work correctly:
                </p>

                <div style="font-size:13px; margin-left:12px;">
                    <code>Suggested Answer: B</code><br>
                    <code>Correct Answer: D</code>
                </div>

                <p style="opacity:.75; font-size:12px; margin-top:8px">
                    The answer letter (<code>A</code>, <code>B</code>, <code>C</code>, etc.) must match one of the listed choices.
                </p>

                <p style="opacity:.75; font-size:12px; margin-top:10px">
                    <strong>Supported example:</strong><br>
                    1. Question text<br>
                    A. Answer<br>
                    B. Answer<br>
                    C. Answer<br>
                    Suggested Answer: B
                </p>

                <p style="opacity:.65; font-size:12px; margin-top:6px">
                    ❌ Answers like <code>B</code> or <code>Answer: B</code> alone will <u>not</u> be detected.
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

                <!-- ========================= -->
                <!--  ADVANCED PARSING UI     -->
                <!--  ONLY SHOW IF ENABLED    -->
                <!-- ========================= -->
                {% if cfg.enable_regex_replace %}

                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">Optional: Regex Replace Rules</h3>

                    <button type="button"
                            onclick="window.open('/static/regex-help.html', '_blank')"
                            title="Fix PDF bullets, wrapped lines, and exam paste issues"
                            style="
                                display:flex;
                                align-items:center;
                                gap:6px;
                                font-size:13px;
                                padding:4px 10px;
                                cursor:pointer;
                            ">
                        <span style="font-size:16px;">❓</span> Regex Help
                    </button>


                </div>


                <p style="opacity:.8; font-size:12px">
                    Runs BEFORE parsing. Format:<br>
                    REGEX => REPLACEMENT<br><br>

                    Examples:<br>
                    ^\\d+\\.\\s* =>   (removes leading "1. ")<br>
                    Question\\s*#\\d+ =>   (removes Question # labels)<br>
                    \\(Choose.*?\\) =>   (removes Choose statement)
                </p>

                <textarea name="replace_rules"
                          placeholder="^\\d+\\.\\s* => 
Question\\s*#\\d+ => "
                          style="width:100%; height:140px; padding:10px; font-size:14px;"></textarea>

                <br><br>

                <h3>✨ Regex Presets (Optional)</h3>
                <p style="opacity:.8; font-size:12px">
                    These presets automatically apply helpful cleanup rules.<br>
                    They will stack with any manual regex rules above.
                </p>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" name="preset_number_prefix" value="1">
                    Remove numbered question prefixes (1., 22., 5. → removed)
                </label>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" name="preset_pdf_spacing" value="1">
                    Fix PDF / Microsoft broken line wrapping & hyphenation
                </label>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" name="preset_headers" value="1">
                    Try to remove page headers / footers
                </label>

                <br><br>
                {% endif %}

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
    """, portal_title=portal_title, cfg=cfg)





# =========================================================
# SMART SUGGESTIONS ENGINE — FINAL CONSOLIDATED
# =========================================================
def build_smart_suggestions(original_text, cleaned_text):
    suggestions = []
    import re

    # Normalize safely
    o = (original_text or "").strip()
    c = (cleaned_text or "").strip()

    # ---------------------------------------
    # 1️⃣ Detect numbered prefixes
    # ---------------------------------------
    if re.search(r"^\s*\d+\.\s+", o, re.MULTILINE):
        suggestions.append({
            "title": "Numbered Questions Detected",
            "detail": "Questions appear to start with numbers like '1. 2. 3.'.",
            "recommend": "Enable Number Prefix Removal preset"
        })

    # ---------------------------------------
    # 2️⃣ PDF WRAP — warn ONLY if CLEANED TEXT still broken
    # ---------------------------------------
    pdf_wrap_detected = False

    # hyphen wrap still present
    if re.search(r"-\s*\n\s*", c):
        pdf_wrap_detected = True

    # mid-sentence linebreak still present
    elif re.search(r"(?<![.!?:])\s*\n\s*[A-Za-z]", c):
        pdf_wrap_detected = True

    if pdf_wrap_detected:
        suggestions.append({
            "title": "Possible PDF Wrap Detected",
            "detail": "Lines appear split mid-sentence.",
            "recommend": "Enable PDF Line Wrapping Fix preset."
        })

    # ---------------------------------------
    # 3️⃣ HEADER / FOOTER repetition detector
    # ---------------------------------------
    lines = [l.strip() for l in o.splitlines() if l.strip()]
    repeats = [l for l in set(lines) if lines.count(l) >= 3]

    if repeats:
        suggestions.append({
            "title": "Repeated Header/Footer Detected",
            "detail": "Document contains repeating page headers or footers.",
            "recommend": "Enable Header/Footer Cleanup preset"
        })

    # ---------------------------------------
    # 4️⃣ MULTIPLE QUESTION COLLAPSE DETECTOR
    # ---------------------------------------
    answer_markers_pattern = re.compile(
        r"(Correct\s*Answer[s]?|Suggested\s*Answer[s]?)",
        re.IGNORECASE
    )

    total_markers = (
        len(answer_markers_pattern.findall(o)) +
        len(answer_markers_pattern.findall(c))
    )

    if total_markers >= 2:
        suggestions.append({
            "title": "Multiple Questions Detected in a Single Block",
            "detail": (
                "Detected multiple answer markers inside one block. "
                "This usually means more than one question exists but "
                "isn't clearly separated. The parser may merge them."
            ),
            "recommend": (
                "Insert a BLANK LINE between each question, "
                "or number them 1., 2., 3."
            )
        })

    # ---------------------------------------
    # 5️⃣ BOM / Unicode trouble detector
    # ---------------------------------------
    trouble_chars = ["\uFEFF", "\u200B", "\u200C", "\u200D", "\u2060"]

    if any(t in o for t in trouble_chars):
        suggestions.append({
            "title": "Hidden Unicode Characters Present",
            "detail": "Detected BOM or zero-width Unicode in source text.",
            "recommend": "Keep Invisible Character Cleanup Enabled"
        })

    # ---------------------------------------
    # 6️⃣ EVERYTHING LOOKS GOOD fallback
    # ---------------------------------------
    if not suggestions:
        suggestions.append({
            "title": "Formatting Looks Excellent",
            "detail": "No structural or formatting problems detected.",
            "recommend": "You can safely continue 👍"
        })

    return suggestions


# =============================
# 12A – STRUCTURAL VALIDATION
# =============================
def quick_structural_scan(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    issues = []
    question_blocks = 0
    current_block_has_answer = False
    current_block_has_correct = False

    for line in lines:
        
        # Detect likely question
        if re.match(r"^\d+[\).\-]?\s", line) or line.lower().startswith("question"):
            question_blocks += 1

            # if previous question existed but had no answer
            if not current_block_has_answer and question_blocks > 1:
                issues.append("A question appears without any A/B/C/D answer choices.")

            current_block_has_answer = False
            current_block_has_correct = False
        
        # Detect answer choices (A–Z supported)
        if re.match(r"^[A-Za-z][\).\-]?\s", line):
            current_block_has_answer = True

        
        # Detect correct answer
        if "correct answer" in line.lower():
            current_block_has_correct = True

    # Final block sanity check
    if question_blocks == 0:
        issues.append("No recognizable questions were detected.")

    if question_blocks > 0 and not current_block_has_answer:
        issues.append("Last detected question has no answer choices.")

    if question_blocks > 0 and not current_block_has_correct:
        issues.append("No 'Correct Answer' lines were found — quiz may fail to grade.")

    return {
        "question_blocks": question_blocks,
        "issues": issues
    }





# =========================
# PREVIEW CLEAN TEXT BEFORE PARSE
# =========================
@app.route("/preview_paste", methods=["POST"])
def preview_paste():
    #cleanup_temp_logos()   # 🧹 optional cleanup (leave commented)

    quiz_text = request.form.get("quiz_text", "").strip()
    quiz_title = request.form.get("quiz_title", "Generated Quiz From Paste")
    strip_rules_raw = request.form.get("strip_text", "").strip()

    # =========================
    # TEMPORARY LOGO HANDLING (PASTE PREVIEW)
    # =========================
    logo_file = request.files.get("quiz_logo")
    temp_logo_name = None

    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            ts = int(time.time())
            temp_logo_name = f"temp_{ts}{ext}"

            temp_dir = os.path.join(app.static_folder, "logos", "_temp")
            os.makedirs(temp_dir, exist_ok=True)

            temp_path = os.path.join(temp_dir, temp_logo_name)
            logo_file.save(temp_path)

            print(f"[LOGO PREVIEW] Saved temp logo → {temp_path}")



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

    # =========================
    # APPLY STRIP RULES (optional regex mode)
    # =========================
    strip_rules = []
    if strip_rules_raw:
        strip_rules = [r.strip() for r in strip_rules_raw.splitlines() if r.strip()]

    cfg = load_portal_config()
    regex_mode = cfg.get("enable_regex_strip", False)
    regex_replace_enabled = cfg.get("enable_regex_replace", False)
    
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
                        # Ignore bad regex patterns
                        pass

                # --- PLAIN TEXT MODE ---
                else:
                    if rule.lower() in test.lower():
                        remove = True
                        break

            if not remove:
                cleaned_lines.append(line)

        clean_text = "\n".join(cleaned_lines)

    # =========================
    # REGEX REPLACE ENGINE
    # =========================
    regex_replace_enabled = cfg.get("enable_regex_replace", False)

    replace_rules_raw = request.form.get("replace_rules", "").strip()
    applied_rules = []

    # -------------------------
    # MANUAL USER REGEX RULES
    # -------------------------
    if regex_replace_enabled and replace_rules_raw:
        for line in replace_rules_raw.splitlines():
            line = line.strip()
            if "=>" not in line:
                continue

            pattern, replacement = line.split("=>", 1)
            pattern = pattern.strip()
            replacement = replacement.strip()

            if not pattern:
                continue

            try:
                new_text = re.sub(
                    pattern,
                    replacement,
                    clean_text,
                    flags=re.IGNORECASE | re.MULTILINE
                )

                if new_text != clean_text:
                    applied_rules.append(pattern)

                clean_text = new_text

            except re.error:
                applied_rules.append(f"[INVALID REGEX] {pattern}")

    # =========================================================
    # REGEX PRESETS (state preserved for the template)
    # =========================================================
    preset_number_prefix_checked = bool(request.form.get("preset_number_prefix"))
    preset_pdf_spacing_checked = bool(request.form.get("preset_pdf_spacing"))
    preset_headers_checked = bool(request.form.get("preset_headers"))

    if regex_replace_enabled:
        preset_patterns = []

    # 1️⃣ Remove numbered prefixes FIRST
    if preset_number_prefix_checked:
        preset_patterns.append((
            r"^\s*\d+\.\s*",
            "",
            "Removed numbered prefixes"
        ))

    # 2️⃣ REMOVE HEADERS / FOOTERS SECOND
    if preset_headers_checked:
        preset_patterns.append((
            r"^\s*(Page\s+\d+.*|Copyright.*|All\s+Rights\s+Reserved.*)$",
            "",
            "Removed header/footer text"
        ))

    # 2️⃣ Fix PDF / Microsoft wrapped lines + hyphenation
    if preset_pdf_spacing_checked:
        preset_patterns.append((
            r"-\s*\n\s*",
            "",
            "Fixed PDF hyphen wraps"
        ))

        # SUPER SAFE PDF WRAP JOIN
        # Will NOT join across question boundaries
        preset_patterns.append((
            r"(?<=[a-z,;])\n(?=\s*[a-z])",
            " ",
            "Joined wrapped lines safely"
        ))





        # ---------- APPLY PRESETS ----------
        for pattern, replacement, label in preset_patterns:
            try:
                new_text = re.sub(
                    pattern,
                    replacement,
                    clean_text,
                    flags=re.IGNORECASE | re.MULTILINE
                )

                if new_text != clean_text:
                    applied_rules.append(label)

                clean_text = new_text

            except re.error:
                applied_rules.append(f"[INVALID PRESET REGEX] {pattern}")

    # =========================
    # AUTO MULTI-QUESTION SPLIT FIX
    # =========================
    safe_split_pattern = re.compile(
        r"(Correct\s*Answer[s]?:.*?\n)(?=\S)",
        re.IGNORECASE
    )

    # Also support Suggested Answer
    safe_split_pattern_2 = re.compile(
        r"(Suggested\s*Answer[s]?:.*?\n)(?=\S)",
        re.IGNORECASE
    )

    new_text = clean_text

    new_text = safe_split_pattern.sub(r"\1\n", new_text)
    new_text = safe_split_pattern_2.sub(r"\1\n", new_text)

    if new_text != clean_text:
        applied_rules.append("Auto Question Splitter")
        clean_text = new_text

    # =========================
    # FORCE MCQ OPTIONS ON CLEAN LINES
    # =========================
    # 1️⃣ Ensure every choice letter starts a new line
    choice_line_fix = re.compile(
        r"\s+(?=([A-Z]\.\s))"
    )

    new_text = clean_text
    new_text = choice_line_fix.sub(r"\n", new_text)

    # 2️⃣ Remove accidental double newlines caused by above
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)

    if new_text != clean_text:
        applied_rules.append("Normalized MCQ Choices")
        clean_text = new_text




    # =========================
    # AUTO BOM / INVISIBLE CLEAN
    # =========================
    invis_cleanup_enabled = cfg.get("auto_bom_clean", False)
    removed_unicode = []

    if invis_cleanup_enabled:
        invisibles = [
            ("\uFEFF", "BOM"),
            ("\u200B", "Zero-Width Space"),
            ("\u200C", "Zero-Width Non-Joiner"),
            ("\u200D", "Zero-Width Joiner"),
            ("\u2060", "Word Joiner"),
        ]

        before = clean_text

        for char, label in invisibles:
            if char in clean_text:
                removed_unicode.append(label)
                clean_text = clean_text.replace(char, "")

        # Normalize multiple blank lines
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        # If BOM only at start
        if before != clean_text and "BOM" not in removed_unicode:
            if before.startswith("\uFEFF"):
                removed_unicode.append("BOM")
                clean_text = clean_text.lstrip("\uFEFF")

    # -------- CONFIDENCE ANALYSIS --------
    conf_summary = conf_details = None
    if get_confidence_setting():
        conf_summary, conf_details = analyze_confidence(clean_text)

    # -------- SMART SUGGESTIONS --------
    smart_suggestions = []

    def add_suggestion(title, detail, recommend, rule=None):
        smart_suggestions.append({
            "title": title,
            "detail": detail,
            "recommend": recommend,
            "suggest_rule": rule
        })

    text = clean_text

    # 1️⃣ Detect wrapped PDF text
    if re.search(r"(?<![.!?])\n(?!\n)", text):
        add_suggestion(
            "Possible PDF Wrap Detected",
            "Lines appear split where they should be continuous sentences.",
            "Enable PDF Line Wrapping Fix preset.",
            "Enable preset: PDF Wrapping"
        )

    # 2️⃣ Detect numbered prefixes like 1. Question
    if re.search(r"^\s*\d+\.\s+", text, re.MULTILINE):
        add_suggestion(
            "Numbered Question Prefixes Found",
            "Detected numbering like '1.' or '22.' before questions.",
            "Enable Number Prefix Removal preset.",
            r"^\s*\d+\.\s* => "
        )

    # 3️⃣ Detect repeated header/footer patterns
    if re.search(r"Page\s+\d+", text) or re.search(r"Copyright", text, re.I):
        add_suggestion(
            "Likely Headers/Footers Detected",
            "Repeated structural text such as page numbers or copyright text found.",
            "Enable Header/Footer Cleanup preset.",
            "Enable preset: Headers"
        )

    # 4️⃣ Detect if nothing changed
    if quiz_text == clean_text:
        add_suggestion(
            "No Formatting Changes Applied",
            "None of your strip or regex rules changed the text.",
            "Try enabling presets or adding regex rules."
        )

    # 5️⃣ If no warnings, say it’s clean
    if len(smart_suggestions) == 0:
        add_suggestion(
            "Formatting Looks Excellent",
            "No structural or formatting problems detected.",
            "You can safely continue 👍"
        )


    # =========================
    # UI SUPPORT LOGIC — ensure template displays correctly
    # =========================

    # If global regex replace enabled but user did not submit rules,
    # keep replace_rules list empty but still treat engine as active
    replace_rules = replace_rules_raw.splitlines() if replace_rules_raw else []

    # Make template show replace rules section when enabled globally
    if regex_replace_enabled and not replace_rules:
        replace_rules = ["(Regex engine enabled — no manual rules entered)"]


    # ---------- RENDER PREVIEW ----------
    return render_template_string("""

<html>
<head>
    <title>Preview Before Parsing</title>
    <link rel="stylesheet" href="/static/style.css">
</head>

<body>

  <script>
    fetch("/config/portal.json")
    .then(r => r.json())
    .then(cfg => {
        if (cfg.background_image) {
            document.documentElement.style.setProperty(
                "--portal-bg",
                `url(${cfg.background_image})`
            );
        }
    });
    </script>
                             

<div class="container">
    
    <h1 class="hero-title">👀 Preview Quiz Before Building</h1>

    <div class="card">
        <h2>Quiz Title:</h2>
        <p><b>{{quiz_title}}</b></p>

        <!-- STEP 7: PRE-PROCESS SUMMARY PANEL -->
<div style="background:#1a1a1a; padding:12px; border-radius:8px; margin-bottom:18px;">
    <h2>🧪 Pre-Processing Summary</h2>

    <!-- =============================
          REGEX STRIP + STRIP RULES
    ============================== -->
    {% if regex_mode %}
    <p><b>Regex Strip Mode:</b> Enabled ✔</p>

        {% if strip_rules %}
        <h3>Lines Removed By Strip Rules</h3>
        <ul>
            {% for r in strip_rules %}
            <li>{{r}}</li>
            {% endfor %}
        </ul>
        {% endif %}
    {% endif %}

    <!-- =============================
          MANUAL REGEX RULES
    ============================== -->
    {% if replace_rules %}
    <h3>Manual Regex Replace Rules</h3>
    <ul>
        {% for r in replace_rules %}
        <li>{{r}}</li>
        {% endfor %}
    </ul>
    {% endif %}

    <!-- =============================
          PRESETS — ONLY IF ANY USED
    ============================== -->
    {% if preset_number_prefix_checked or preset_pdf_spacing_checked or preset_headers_checked %}
    <h3>✨ Regex Presets</h3>
    <ul>
        {% if preset_number_prefix_checked %}
        <li>Number Prefix Removal Enabled ✔</li>
        {% endif %}

        {% if preset_pdf_spacing_checked %}
        <li>PDF Line Wrapping Fix Enabled ✔</li>
        {% endif %}

        {% if preset_headers_checked %}
        <li>Header/Footer Cleanup Enabled ✔</li>
        {% endif %}
    </ul>
    {% endif %}

    <!-- =============================
          RULES THAT ACTUALLY FIRED
    ============================== -->
    {% if applied_rules %}
    <h3>Rules That Actually Changed Text</h3>
    <ul>
        {% for r in applied_rules %}
        <li>✔ {{r}}</li>
        {% endfor %}
    </ul>
    {% endif %}

    <!-- =============================
          INVISIBLE CLEAN
    ============================== -->
    {% if invis_cleanup_enabled %}
    <h3>Invisible Character Cleanup</h3>

        {% if removed_unicode %}
        <p>Removed:</p>
        <ul>
            {% for u in removed_unicode %}
            <li>{{u}}</li>
            {% endfor %}
        </ul>
        {% else %}
        <p>No hidden Unicode issues found 🎉</p>
        {% endif %}
    {% endif %}
</div>


                       <!-- SMART SUGGESTIONS -->
                    <h3>💡 Smart Suggestions</h3>

                    {% if smart_suggestions and smart_suggestions|length > 0 %}
                    <ul>
                    {% for s in smart_suggestions %}
                    <li style="margin-bottom:10px;">
                        <b>{{s.title}}</b><br>
                        <span style="opacity:.85">{{s.detail}}</span><br>
                        <span style="opacity:.7">Recommendation: {{s.recommend}}</span>

                        {% if s.suggest_rule %}
                        <br>
                        <code style="background:#222;padding:4px 6px;border-radius:6px;">
                            {{s.suggest_rule}}
                        </code>
                        {% endif %}

                        <!-- APPLY BUTTON -->
                        <form action="/preview_paste" method="POST" style="margin-top:8px;">

                            <!-- always resend original data -->
                            <input type="hidden" name="quiz_title" value="{{quiz_title}}">
                            <textarea name="quiz_text" style="display:none;">{{original}}</textarea>

                            <!-- preserve user cleanup fields if they existed -->
                            <textarea name="strip_text" style="display:none;">
                    {% for r in strip_rules %}{{r}}
                    {% endfor %}
                            </textarea>

                            <textarea name="replace_rules" style="display:none;">
                    {% for r in replace_rules %}{{r}}
                    {% endfor %}
                            </textarea>

                            <!-- turn on correct preset -->
                            {% if "PDF" in s.title %}
                                <input type="hidden" name="preset_pdf_spacing" value="1">
                            {% endif %}

                            {% if "Number" in s.title %}
                                <input type="hidden" name="preset_number_prefix" value="1">
                            {% endif %}

                            {% if "Header" in s.title or "Footer" in s.title %}
                                <input type="hidden" name="preset_headers" value="1">
                            {% endif %}

                            <button type="submit">⚙ Apply This Fix</button>
                        </form>

                    </li>
                    {% endfor %}
                    </ul>
                    {% else %}
                    <p>No suggestions — formatting already looks great 🎯</p>
                    {% endif %}


        </div>
        <!-- END SUMMARY -->

        <h2>Original Text</h2>
        <pre id="origBox" style="background:black;padding:10px;border-radius:8px;white-space:pre-wrap;">{{original}}</pre>

        <h2>Text To Be Parsed: (passed to quiz)</h2>
        <pre id="cleanBox" style="background:#102020;padding:10px;border-radius:8px;white-space:pre-wrap;">{{cleaned}}</pre>

        <br>
        <button onclick="toggleInvisible()" style="margin-top:5px;">
            👁 Show / Hide Invisible Characters
        </button>

        <p style="opacity:.7">
            This helps detect BOM, zero-width, Unicode junk, and newline issues.
        </p>

        <div id="visualPanel" style="display:none; margin-top:15px;">
            <h2>🔍 Visualized Text</h2>

            <h3>Original Input</h3>
            <pre id="visualOrig" style="background:#222;padding:10px;border-radius:8px;white-space:pre-wrap;"></pre>

            <h3>Parsed (Cleaned) Version</h3>
            <pre id="visualClean" style="background:#333;padding:10px;border-radius:8px;white-space:pre-wrap;"></pre>
        </div>

        <script>
        function visualize(text) {
            return text
                .replace(/\\u200B/g, "[ZWSP]")
                .replace(/\\u200C/g, "[ZWNJ]")
                .replace(/\\u200D/g, "[ZWJ]")
                .replace(/\\u2060/g, "[WJ]")
                .replace(/\\uFEFF/g, "[BOM]")
                .replace(/ /g, "·")
                .replace(/\\n/g, "\\\\n\\n");
        }

        function toggleInvisible() {
            const panel = document.getElementById("visualPanel");
            const show = panel.style.display === "none";

            if (show) {
                document.getElementById("visualOrig").innerText =
                    visualize(document.getElementById("origBox").innerText);

                document.getElementById("visualClean").innerText =
                    visualize(document.getElementById("cleanBox").innerText);
            }

            panel.style.display = show ? "block" : "none";
        }
        </script>

        <!-- 🔍 DIFF VIEW -->
        <button onclick="toggleDiff()" style="margin-top:10px;">
            🔍 Show / Hide Differences
        </button>

        <div id="diffPanel" style="display:none; margin-top:15px;">
            <h2>⚖️ Text Differences</h2>

            <h3>Original vs Cleaned Comparison</h3>
            <pre id="diffView"
                 style="background:#252525;padding:10px;border-radius:8px;white-space:pre-wrap;"></pre>

            <p style="opacity:.7">
                <span style="color:#4cff4c;font-weight:bold;">Green</span> = added ·
                <span style="color:#ff4c4c;font-weight:bold;">Red</span> = removed
            </p>

        </div>

        <script>
function toggleDiff() {
    const panel = document.getElementById("diffPanel");
    const show = panel.style.display === "none";
    if (show) runDiff();
    panel.style.display = show ? "block" : "none";
}

function normalizeKey(s) {
    return (s || "")
        .replace(/\\r/g, "")
        .replace(/[\\u200B\\u200C\\u200D\\u2060]/g, "")
        .replace(/\\uFEFF/g, "")
        .replace(/\\u00A0/g, " ")
        .replace(/\\s+/g, " ")
        .trim();
}

function runDiff() {
    const origLines = document.getElementById("origBox").innerText
        .split("\\n")
        .map(normalizeKey)
        .filter(Boolean);

    const cleanLines = document.getElementById("cleanBox").innerText
        .split("\\n")
        .map(normalizeKey)
        .filter(Boolean);

    let out = "";

    // REMOVED
    for (const line of origLines) {
        if (!cleanLines.includes(line)) {
            out += "<span class='diff-removed'>[REMOVED] " + line + "</span><br>";


        }
    }

    // ADDED
    for (const line of cleanLines) {
        if (!origLines.includes(line)) {
            out += "<span class='diff-added'>[ADDED] " + line + "</span><br>";


        }
    }

    if (!out.trim()) {
        out = "No structural differences detected.";
    }

    document.getElementById("diffView").innerHTML = out;
}
</script>



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
            <input type="hidden" name="quiz_title" value="{{ quiz_title }}">
            <input type="hidden" name="temp_logo_name" value="{{ temp_logo_name }}">
            <textarea name="quiz_text" style="display:none;">{{ cleaned }}</textarea>

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
        temp_logo_name=temp_logo_name,
        regex_mode=regex_mode,
        strip_rules=strip_rules,
        replace_rules=replace_rules,   # <-- FIXED
        applied_rules=applied_rules,
        invis_cleanup_enabled=invis_cleanup_enabled,
        removed_unicode=removed_unicode,
        preset_number_prefix_checked=preset_number_prefix_checked,
        preset_pdf_spacing_checked=preset_pdf_spacing_checked,
        preset_headers_checked=preset_headers_checked,
        smart_suggestions=smart_suggestions
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
    #cleanup_temp_logos()   # 🧹 clean abandoned logos again

    quiz_text = request.form.get("quiz_text", "").strip()
    quiz_title = request.form.get("quiz_title", "Generated Quiz From Paste")

    # Checkbox flag (Auto Junk Cleanup)
    auto_cleanup = request.form.get("auto_cleanup") == "1"

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

    # Optional auto cleanup (only runs if you wire a checkbox)
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

    # Save cleaned text (for debugging / consistency)
    path = os.path.join(UPLOAD_FOLDER, "pasted.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # =========================
    # PARSE QUIZ
    # =========================
    quiz_data = parse_questions(clean_text)

    # Always save a parse log (success or failure)
    ts = int(time.time())
    log_filename = f"parse_log_{ts}.txt"
    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

    # If no questions parsed, show failure UI + log link
    if not quiz_data:
        return render_template_string("""
        <html>
        <head>
            <title>Parse Failed</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
        <script>
        fetch("/config/portal.json")
        .then(r => r.json())
        .then(cfg => {
            if (cfg.background_image) {
                document.documentElement.style.setProperty(
                    "--portal-bg",
                    `url(${cfg.background_image})`
                );
            }
        });
        </script>

        <div class="container">
            <h1 class="hero-title">⚠️ Could Not Parse Any Questions</h1>

            <div class="card">
                <p>No valid questions were parsed. Please check the formatting.</p>
                <p>You can download the parser log for troubleshooting:</p>

                <button onclick="location.href='/data/{{log_filename}}'">
                    📥 Download Parse Log
                </button>

                <br><br>

                <button onclick="location.href='/upload'">
                    ⬅ Back To Upload Page
                </button>

                <button onclick="location.href='/paste'">
                    📋 Try Paste Mode Instead
                </button>

                <button onclick="location.href='/'">
                    🏠 Return To Portal
                </button>
            </div>
        </div>
        </body>
        </html>
        """, log_filename=log_filename), 400

    # =========================
    # HANDLE LOGO (FINAL, SINGLE SOURCE OF TRUTH)
    # =========================
    logo_filename = None

    logo_file = request.files.get("quiz_logo")
    temp_logo_name = request.form.get("temp_logo_name")

    # Case 1: Finalize temp logo from preview
    if temp_logo_name and temp_logo_name.lower() != "none":
        temp_dir = os.path.join(app.static_folder, "logos", "_temp")
        src = os.path.join(temp_dir, temp_logo_name)

        if os.path.exists(src):
            ext = os.path.splitext(temp_logo_name)[1].lower()
            logo_filename = f"logo_{ts}{ext}"

            final_dir = os.path.join(app.static_folder, "logos")
            os.makedirs(final_dir, exist_ok=True)

            dst = os.path.join(final_dir, logo_filename)
            os.rename(src, dst)

            print(f"[LOGO] Finalized logo → {dst}")
        else:
            print("[LOGO WARNING] Temp logo missing:", src)



    # Case 2: Direct upload (no preview)
    elif logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            logo_filename = f"logo_{ts}{ext}"
            dst = os.path.join(STATIC_LOGO_FOLDER, logo_filename)
            logo_file.save(dst)

            print(f"[LOGO] Uploaded logo → {dst}")

    # SAFETY CHECK
    if logo_filename:
        final_path = os.path.join(app.static_folder, "logos", logo_filename)
        if not os.path.exists(final_path):
            print("[LOGO ERROR] Logo filename set but file missing:", final_path)
            logo_filename = None


    # =========================
    # SAVE QUIZ
    # =========================
    source_file = f"quiz_{ts}.html"

    save_quiz_to_db(
        quiz_title,
        source_file,
        quiz_data,
        logo_filename
    )




   # =========================
    # SAVE JSON + HTML quiz (kept for UI compatibility)
    # =========================
    json_name = f"quiz_{ts}.json"
    html_name = f"quiz_{ts}.html"

    with open(os.path.join(DATA_FOLDER, json_name), "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=4)

    # =========================
    # REGISTER QUIZ (AFTER html_name EXISTS)
    # =========================
    dprint("[DEBUG] Registering quiz:",
        html_name,
        quiz_title,
        logo_filename)

    add_quiz_to_registry(
        html_name,
        quiz_title,
        logo_filename
    )


    build_quiz_html(
        html_name,
        json_name,
        os.path.join(QUIZ_FOLDER, html_name),
        get_portal_title(),
        quiz_title,
        logo_filename
    )

    # FINAL SAFETY: only register logo if file actually exists
    if logo_filename:
        final_logo_path = os.path.join(LOGO_FOLDER, logo_filename)
        if not os.path.exists(final_logo_path):
            dprint("[LOGO FIX] Prevented registering missing logo:", logo_filename)
            logo_filename = None

    #add_quiz_to_registry(html_name, quiz_title, logo_filename)

    return redirect("/library")



@app.route("/process", methods=["POST"])
def process_file():
    #cleanup_temp_logos()  # 🧹 clean abandoned logos
    file = request.files.get("file")
    quiz_title = request.form.get("quiz_title", "Generated Quiz")
    quiz_logo = request.files.get("quiz_logo")

    logo_filename = None  # ✅ ensure always defined
    source_file = None    # ✅ canonical quiz identifier

    if not file:
        return "No file uploaded", 400

    # ---- determine source_file (required by schema) ----
    if file.filename:
        source_file = file.filename
    else:
        source_file = f"manual_paste_{int(time.time())}"

    # ---- save uploaded text file ----
    path = os.path.join(UPLOAD_FOLDER, source_file)
    file.save(path)



    # =========================
    # READ FILE CONTENT (CRITICAL FIX)
    # =========================
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read().strip()

    if not raw_text:
        return "Uploaded file is empty.", 400

    # Normalize ALL newline styles (MATCH PASTE MODE)
    clean_text = (
        raw_text
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    # =========================
    # PARSE QUIZ (SAME AS PASTE MODE)
    # =========================
    quiz_data = parse_questions(clean_text)

    # Always save a parse log (success or failure)
    ts = int(time.time())
    log_filename = f"parse_log_{ts}.txt"
    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

    if not quiz_data:
        return render_template_string("""
        <html>
        <head>
            <title>Parse Failed</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
        <script>
        fetch("/config/portal.json")
        .then(r => r.json())
        .then(cfg => {
            if (cfg.background_image) {
                document.documentElement.style.setProperty(
                    "--portal-bg",
                    `url(${cfg.background_image})`
                );
            }
        });
        </script>

        <div class="container">
            <h1 class="hero-title">⚠️ Could Not Parse Any Questions</h1>

            <div class="card">
                <p>No valid questions were parsed. Please check the formatting.</p>
                <p>You can download the parser log for troubleshooting:</p>

                <button onclick="location.href='/data/{{log_filename}}'">
                    📥 Download Parse Log
                </button>

                <br><br>

                <button onclick="location.href='/upload'">
                    ⬅ Back To Upload Page
                </button>

                <button onclick="location.href='/paste'">
                    📋 Try Paste Mode Instead
                </button>

                <button onclick="location.href='/'">
                    🏠 Return To Portal
                </button>
            </div>
        </div>
        </body>
        </html>
        """, log_filename=log_filename), 400

    print("UPLOAD MODE FINAL PARSE COUNT:", len(quiz_data))

    # =========================
    # PARSE DIAGNOSTICS (TEMP)
    # =========================
    for i, q in enumerate(quiz_data, 1):
        choices = q.get("choices", [])
        has_correct = any(c.get("is_correct") for c in choices)

        if not choices or not has_correct:
            dprint(f"[PARSE WARNING] Q{i} missing choices or correct answer")


    # =========================
    # HANDLE LOGO
    # =========================
    logo_filename = None
    if quiz_logo and quiz_logo.filename:
        ext = os.path.splitext(quiz_logo.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            logo_filename = f"logo_{ts}{ext}"

            # Always save upload logos into Flask-served static folder
            static_logo_dir = os.path.join(app.static_folder, "logos")
            os.makedirs(static_logo_dir, exist_ok=True)

            dst = os.path.join(static_logo_dir, logo_filename)
            quiz_logo.save(dst)

            print(f"[LOGO] Uploaded logo → {dst}")

            # Safety check (prevents silent broken images)
            if not os.path.exists(dst):
                print("[LOGO ERROR] Upload logo missing after save:", dst)
                logo_filename = None

    save_quiz_to_db(quiz_title, source_file, quiz_data, logo_filename)



    # =========================
    # SAVE JSON + HTML quiz (UI compatibility)
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

    return redirect("/library")




@app.route("/settings")
def settings_page():
    cfg = load_portal_config()

    # Ensure safe defaults if missing from portal.json
    cfg.setdefault("show_confidence", True)
    cfg.setdefault("enable_regex_replace", False)
    cfg.setdefault("auto_bom_clean", False)
    cfg.setdefault("enable_show_invisibles", True)

    return render_template_string("""
<html>
<head>
<title>Portal Settings</title>
<link rel="stylesheet" href="/static/style.css">
</head>

<body>
                                  
<script>
fetch("/config/portal.json")
  .then(r => r.json())
  .then(cfg => {
      if (cfg.background_image) {
          document.documentElement.style.setProperty(
              "--portal-bg",
              `url(${cfg.background_image})`
          );
      }
  });
</script>



<div class="container">

    <h1 class="hero-title">
        ⚙️ Portal Configuration
    </h1>

    <div class="card">

        <!-- NOTE: enctype added so we can upload files -->
        <form action="/save_settings" method="POST" enctype="multipart/form-data">

            <!-- ============================
                 PORTAL TITLE
                 ============================ -->
            <h3>Training Portal Title</h3>
            <input type="text"
                   name="portal_title"
                   value="{{cfg.title}}"
                   required style="width:100%; padding:6px">

            <br><br>

            <!-- ============================
                 BACKGROUND IMAGE UPLOAD
                 ============================ -->
            <h3>Background Image (Optional)</h3>
            <p style="opacity:.75; font-size:13px">
                This image is used as the main background for the entire site.
                For best results, use:
            </p>
            <ul style="opacity:.8; font-size:13px; margin-top:2px;">
                <li>Landscape image (wider than tall)</li>
                <li>Minimum 1600×900 (Full HD 1920×1080 recommended)</li>
                <li>JPG or PNG, preferably under 3–4 MB</li>
                <li>Not too bright or busy (subtle textures work best)</li>
            </ul>

            <input type="file"
                   name="background_image"
                   accept="image/*"
                   style="margin-top:6px;">

            <br><br>

            <!-- ============================
                 ADVANCED PARSING TOGGLE
                 ============================ -->
            <button type="button"
                    id="toggleAdvancedBtn"
                    style="margin-top:10px;">
                🔧 Show Advanced Parsing Settings
            </button>

            <div id="advParsingPanel"
                 style="margin-top:15px; display:none; padding:12px; border-radius:8px;
                        background:rgba(0,0,0,0.6); border:1px solid rgba(255,255,255,0.25);">

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

                <h3>Regex Strip / Replace Engine</h3>
                <p style="opacity:.7">
                    Enables advanced REGEX-based cleanup tools when pasting quiz content.
                </p>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" name="enable_regex_replace"
                           value="1"
                           {% if cfg.enable_regex_replace %}checked{% endif %}>
                    Enable Regex Replace Engine
                </label>

                <br><br>

                <h3>Invisible / BOM Cleanup</h3>
                <p style="opacity:.7">
                    Automatically removes BOM characters, zero-width spaces, and hidden Unicode junk
                    that can break parsing when copying text from PDFs or Microsoft Word.
                </p>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox"
                           name="auto_bom_clean"
                           value="1"
                           {% if cfg.auto_bom_clean %}checked{% endif %}>
                    Enable Invisible Character & BOM Cleanup
                </label>

                <br><br>

                <h3>Show Invisible Characters Tool</h3>
                <p style="opacity:.7">
                    Allows user to toggle visualization of hidden characters during preview.
                </p>

                <label style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox"
                        name="enable_show_invisibles"
                        value="1"
                        {% if cfg.enable_show_invisibles %}checked{% endif %}>
                    Enable "Show Invisible Characters" Debug Tool
                </label>

            </div> <!-- /advParsingPanel -->

            <br><br>

            <button type="submit">💾 Save Settings</button>
        </form>

        <br>

        <hr>

        <h3>Persistent Exam Storage</h3>
        <p style="opacity:.75">
            These results are stored in the application database.  
            Clearing will permanently delete all recorded attempts and missed-question history.
        </p>

        <button id="clearDBBtn" style="
            background:#ff4d4d;
            color:white;
            padding:10px 14px;
            border-radius:8px;
            border:1px solid rgba(255,255,255,.3);
        ">
            🗑 Clear Saved Permanent Results (Database)
        </button>

        <p id="clearDBStatus" style="margin-top:6px;"></p>

        <br>
        <button onclick="location.href='/'">⬅ Back To Portal</button>

    </div>

    <script>
    // Toggle Advanced Parsing Panel
    (function() {
        const btn  = document.getElementById("toggleAdvancedBtn");
        const panel = document.getElementById("advParsingPanel");
        if (!btn || !panel) return;

        let open = false;
        btn.addEventListener("click", () => {
            open = !open;
            panel.style.display = open ? "block" : "none";
            btn.textContent = open
                ? "🔧 Hide Advanced Parsing Settings"
                : "🔧 Show Advanced Parsing Settings";
        });
    })();

    // Clear DB history button
    document.getElementById("clearDBBtn").addEventListener("click", async () => {

        if (!confirm(
            "⚠ This will permanently delete ALL saved exam results and missed question records.\\n\\nThis cannot be undone.\\n\\nContinue?"
        )) return;

        try {
            const res = await fetch("/api/clear_db_history", { method: "POST" });
            const data = await res.json();

            if (data.status === "ok") {
                document.getElementById("clearDBStatus").innerText =
                    "✅ Persistent history deleted successfully";
                alert("Persistent DB history cleared!");
                location.reload();
            } else {
                throw new Error();
            }

        } catch (err) {
            document.getElementById("clearDBStatus").innerText =
                "⚠️ Failed to clear persistent history.";
        }
    });
    </script>

</div>
</body>
</html>
    """, cfg=cfg)







def load_portal_config():
    """Always returns a valid portal config dict."""
    default = {
        "title": "Training & Practice Center",
        "show_confidence": True,
        "enable_regex_replace": False,
        "auto_bom_clean": False,
        "enable_show_invisibles": False,
    }

    if not os.path.exists(PORTAL_CONFIG):
        return default

    try:
        with open(PORTAL_CONFIG, "r") as f:
            data = json.load(f)

        # 🔄 Backward compatibility: if old key exists, map it
        if "auto_clean_hidden" in data and "auto_bom_clean" not in data:
            data["auto_bom_clean"] = bool(data.get("auto_clean_hidden"))

        return {
            "title": data.get("title", default["title"]),
            "show_confidence": data.get("show_confidence", default["show_confidence"]),
            "enable_regex_replace": data.get("enable_regex_replace", default["enable_regex_replace"]),
            "auto_bom_clean": data.get("auto_bom_clean", default["auto_bom_clean"]),
            "enable_show_invisibles": data.get("enable_show_invisibles", default["enable_show_invisibles"]),
        }
    except:
        return default




@app.route("/save_settings", methods=["POST"])
def save_settings():
    cfg = load_portal_config()

    dprint("\n[SETTINGS] ===== SAVE_SETTINGS CALLED =====")
    dprint("[SETTINGS] Incoming form keys:", list(request.form.keys()))
    dprint("[SETTINGS] Incoming file keys:", list(request.files.keys()))
    dprint("[SETTINGS] PORTAL_CONFIG path:", PORTAL_CONFIG)
    dprint("[SETTINGS] Existing config BEFORE update:", cfg)

    # =========================
    # Portal title
    # =========================
    title = request.form.get("portal_title", cfg.get("title", "Training Portal")).strip()
    cfg["title"] = title
    dprint("[SETTINGS] Updated title:", title)

    # =========================
    # Advanced toggles
    # =========================
    cfg["show_confidence"]        = ("show_confidence" in request.form)
    cfg["enable_regex_replace"]   = ("enable_regex_replace" in request.form)
    cfg["auto_bom_clean"]         = ("auto_bom_clean" in request.form)
    cfg["enable_show_invisibles"] = ("enable_show_invisibles" in request.form)

    dprint("[SETTINGS] Toggles:", {
        "show_confidence": cfg["show_confidence"],
        "enable_regex_replace": cfg["enable_regex_replace"],
        "auto_bom_clean": cfg["auto_bom_clean"],
        "enable_show_invisibles": cfg["enable_show_invisibles"],
    })

    # =========================
    # BACKGROUND IMAGE UPLOAD
    # =========================
    file = request.files.get("background_image")

    if file:
        dprint("[SETTINGS] Background file received:", file.filename)

    if file and file.filename.strip():
        filename = secure_filename(file.filename)

        # Ensure folder exists
        os.makedirs(BACKGROUND_FOLDER, exist_ok=True)
        dprint("[SETTINGS] BACKGROUND_FOLDER:", BACKGROUND_FOLDER)

        save_path = os.path.join(BACKGROUND_FOLDER, filename)
        file.save(save_path)

        cfg["background_image"] = f"/static/bg/{filename}"

        dprint("[SETTINGS] Background saved to:", save_path)
        dprint("[SETTINGS] background_image set to:", cfg["background_image"])
    else:
        dprint("[SETTINGS] No background image uploaded this request")

    # =========================
    # SAVE CONFIG
    # =========================
    try:
        with open(PORTAL_CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        dprint("[SETTINGS] Config successfully written to disk")
    except Exception as e:
        print("[SETTINGS][ERROR] Failed to write portal config:", e)

    dprint("[SETTINGS] Final config AFTER update:", cfg)
    dprint("[SETTINGS] ===== SAVE_SETTINGS COMPLETE =====\n")

    return redirect("/settings")






# =====================================================
# RECORD QUIZ ATTEMPT (ID-FIRST, SAFE TITLE FALLBACK)
# =====================================================
@app.route("/record_attempt", methods=["POST"])
def record_attempt():
    data = request.get_json(force=True) or {}
    print("📩 Incoming Attempt Payload:", json.dumps(data, indent=2))

    attempt_id = data.get("attemptId")
    quiz_id = data.get("quizId")
    quiz_title = data.get("quizTitle")

    score = data.get("score", 0)
    total = data.get("total", 0)
    percent = data.get("percent", 0)

    started_at = data.get("startedAt")
    completed_at = data.get("completedAt")
    time_remaining = data.get("timeRemaining")
    mode = data.get("mode", "Exam")

    if not attempt_id:
        return {"error": "Missing attemptId"}, 400

    conn = get_db()
    cur = conn.cursor()

    try:
        # -----------------------------
        # RESOLVE QUIZ ID
        # -----------------------------
        if quiz_id:
            cur.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
            if not cur.fetchone():
                raise Exception(f"Quiz ID {quiz_id} does not exist")
        else:
            if not quiz_title:
                raise Exception("Missing quizId and quizTitle")

            cur.execute("""
                SELECT id
                FROM quizzes
                WHERE title = ?
                ORDER BY id DESC
                LIMIT 1
            """, (quiz_title,))
            row = cur.fetchone()
            if not row:
                raise Exception(f"No quiz found for title '{quiz_title}'")
            quiz_id = row["id"]

        print(f"Saving attempt: attempt_id={attempt_id} quiz_id={quiz_id}")

        # -----------------------------
        # INSERT ATTEMPT
        # -----------------------------
        cur.execute("""
            INSERT INTO attempts (
                id, quiz_id, started_at, completed_at,
                score, total, percent, time_remaining, mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt_id,
            quiz_id,
            started_at,
            completed_at,
            score,
            total,
            percent,
            time_remaining,
            mode,
        ))

        # -----------------------------
        # INSERT MISSED QUESTIONS (FULL SNAPSHOT)
        # -----------------------------
        for m in data.get("missedDetails", []):
            dprint("🧪 MISSED QUESTION RAW:", json.dumps(m, indent=2))

            attempt_qnum = m.get("attemptQuestionNumber", m.get("number"))
            if attempt_qnum is None:
                raise Exception(f"Missing attemptQuestionNumber: {m}")

            # ---- FULL CHOICES SNAPSHOT ----
            choices_lines = []
            for c in m.get("choices", []):
                label = c.get("label")
                text = c.get("text")
                if label and text:
                    choices_lines.append(f"{label} — {text}")

            choices_text = "\n".join(choices_lines)

            dprint("🧪 SNAPSHOT choices_text:")
            dprint(choices_text if choices_text else "(no choices present)")

            cur.execute("""
                INSERT INTO missed_questions (
                    attempt_id,
                    correct_letters,
                    question_text,
                    choices_text,
                    selected_letters,
                    selected_text,
                    correct_text,
                    attempt_question_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_id,
                ",".join(m.get("correctLetters", [])),
                m.get("question"),
                choices_text,
                ",".join(m.get("selectedLetters", [])),
                "\n".join(m.get("selectedText", [])),
                "\n".join(m.get("correctText", [])),
                attempt_qnum
            ))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
        return {"status": "db_error", "detail": str(e)}, 500

    finally:
        conn.close()









@app.route("/api/attempts")
def api_attempts():
    conn = get_db()
    cur = conn.cursor()

    # Load attempts
    cur.execute("""
        SELECT a.id,
               a.quiz_id,
               q.title AS quiz_title,
               a.score,
               a.total,
               a.percent,
               a.started_at,
               a.completed_at,
               a.time_remaining,
               a.mode
        FROM attempts a
        LEFT JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.completed_at DESC
    """)
    attempts = [dict(row) for row in cur.fetchall()]

    # Attach missed questions
    for attempt in attempts:
        cur.execute("""
            SELECT
                attempt_question_number,
                question_text,
                correct_letters,
                correct_text,
                selected_letters,
                selected_text
            FROM missed_questions
            WHERE attempt_id = ?
            ORDER BY attempt_question_number
        """, (attempt["id"],))

        mq = cur.fetchall()


        attempt["missedQuestions"] = [
        {
            "number": m["attempt_question_number"],
            "question": m["question_text"],
            "correctLetters": (m["correct_letters"] or "").split(","),
            "correctText": (m["correct_text"] or "").split("\n"),
            "selectedLetters": (m["selected_letters"] or "").split(","),
            "selectedText": (m["selected_text"] or "").split("\n"),
        }
        for m in mq
    ]



    conn.close()
    return jsonify({"attempts": attempts})


# =====================================================
# ANKI EXPORT HELPERS
# =====================================================

import genanki
import random
import os
import tempfile
import html


def export_quiz_to_apkg(deck_name, deck_rows):
    """
    deck_rows = [
        {
            "front": str,
            "back": str
        }
    ]
    """

    model = genanki.Model(
        1607392319,
        "AutoQuiz Model",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "<hr id='answer'>{{Back}}",
            },
        ],
    )

    deck = genanki.Deck(
        random.randrange(1 << 30, 1 << 31),
        deck_name,
    )

    for row in deck_rows:
        # Escape FIRST (prevents invalid HTML warnings)
        front = html.escape(row.get("front") or "")
        back = html.escape(row.get("back") or "")

        # THEN restore intended formatting
        front = front.replace("\n", "<br>")
        back = back.replace("\n", "<br>")

        note = genanki.Note(
            model=model,
            fields=[front, back],
        )

        deck.add_note(note)

    fd, path = tempfile.mkstemp(suffix=".apkg")
    os.close(fd)

    genanki.Package(deck).write_to_file(path)

    return path








def export_anki_tsv_for_quiz(quiz_id: int) -> str:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            q.number AS question_number,
            q.text   AS question_text,
            qu.title AS quiz_title,
            GROUP_CONCAT(
                c.label || '. ' || c.text,
                CHAR(10)
            ) AS choices,
            GROUP_CONCAT(
                CASE WHEN c.is_correct = 1 THEN c.label END,
                ', '
            ) AS correct_letters,
            GROUP_CONCAT(
                CASE WHEN c.is_correct = 1 THEN c.label || '. ' || c.text END,
                CHAR(10)
            ) AS correct_text
        FROM questions q
        JOIN quizzes qu ON qu.id = q.quiz_id
        JOIN choices c ON c.question_id = q.id
        WHERE q.quiz_id = ?
        GROUP BY q.id
        ORDER BY q.number
    """, (quiz_id,))

    rows = cur.fetchall()
    conn.close()

    lines = ["Front\tBack\tTags"]

    for r in rows:
        # ---------- FRONT ----------
        front = (
            f"<b>{r['question_text']}</b><br><br>"
            + "<br>".join((r["choices"] or "").split("\n"))
        ).replace("\t", " ")

        # ---------- BACK ----------
        back = (
            f"<b>Correct answer:</b> {r['correct_letters']}<br><br>"
            + "<br>".join((r["correct_text"] or "").split("\n"))
        ).replace("\t", " ")

        # ---------- TAGS ----------
        quiz_tag = (r["quiz_title"] or "autoquiz").replace(" ", "_")
        tags = quiz_tag

        lines.append(f"{front}\t{back}\t{tags}")

    return "\n".join(lines)


from flask import Response, request, send_file
import logging

logger = logging.getLogger(__name__)


# =====================================================
# EXPORT FULL QUIZ → TSV (DIRECT DOWNLOAD)
# =====================================================
@app.route("/export/anki/quiz/<int:quiz_id>")
def export_anki_quiz_tsv(quiz_id):
    tsv = export_anki_tsv_for_quiz(quiz_id)

    logger.info("[ANKI-TSV] Export quiz TSV | quiz_id=%s | bytes=%s",
                quiz_id, len(tsv.encode("utf-8")))

    return Response(
        tsv,
        mimetype="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=quiz_{quiz_id}_anki.tsv"
        }
    )


# =====================================================
# EXPORT MISSED QUESTIONS → GENANKI (.apkg)
# =====================================================
@app.route("/export/anki", methods=["POST"])
def export_anki_genanki():
    data = request.get_json(force=True) or {}

    attempt_id = data.get("attempt_id")
    attempt_qnums = data.get("attempt_question_numbers") or data.get("question_numbers") or []

    if not attempt_id or not attempt_qnums:
        return {"error": "Missing attempt_id or question numbers"}, 400

    attempt_qnums = [int(x) for x in attempt_qnums]
    q_marks = ",".join("?" for _ in attempt_qnums)

    conn = get_db()
    cur = conn.cursor()

    # 🔑 IMPORTANT: use SNAPSHOT DATA ONLY
    cur.execute(
        f"""
        SELECT
            mq.attempt_question_number,
            mq.question_text,
            mq.choices_text,
            mq.correct_text,
            qu.title AS quiz_title
        FROM missed_questions mq
        JOIN attempts a ON a.id = mq.attempt_id
        JOIN quizzes qu ON qu.id = a.quiz_id
        WHERE mq.attempt_id = ?
          AND mq.attempt_question_number IN ({q_marks})
        ORDER BY mq.attempt_question_number
        """,
        [attempt_id, *attempt_qnums]
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"error": "No missed questions found"}, 404

    print(f"[ANKI] exporting {len(rows)} missed questions")

    # -----------------------------
    # Transform rows for genanki
    # -----------------------------
    deck_rows = []

    for r in rows:
        question = (r["question_text"] or "").strip()
        choices_text = (r["choices_text"] or "").strip()
        correct_text = (r["correct_text"] or "").strip()

        # FRONT = question + ALL choices
        front_parts = [question]
        if choices_text:
            front_parts.append("")
            front_parts.append(choices_text)

        front = "\n".join(front_parts)

        # BACK = correct answer(s) only
        back = "Correct Answer\n" + correct_text

        deck_rows.append({
            "front": front,
            "back": back
        })

    deck_name = rows[0]["quiz_title"] or "DLMS Missed Questions"

    apkg_path = export_quiz_to_apkg(deck_name, deck_rows)

    return send_file(
        apkg_path,
        as_attachment=True,
        download_name="dlms_missed_questions.apkg",
        mimetype="application/octet-stream"
    )






# =====================================================
# EXPORT MISSED QUESTIONS → TSV (ANKI IMPORT)
# =====================================================
@app.route("/export/anki/missed", methods=["POST"])
def export_anki_missed_tsv():
    data = request.get_json(force=True) or {}

    attempt_id = data.get("attempt_id")
    attempt_qnums = data.get("attempt_question_numbers") or data.get("question_numbers") or []

    if not attempt_id or not attempt_qnums:
        return {"error": "Missing attempt_id or attempt_question_numbers"}, 400

    attempt_qnums = [int(x) for x in attempt_qnums]

    conn = get_db()
    cur = conn.cursor()

    q_marks = ",".join("?" for _ in attempt_qnums)

    cur.execute(
        f"""
        SELECT
            mq.attempt_question_number,
            q.number AS question_number,
            q.text AS question_text,
            (
                SELECT GROUP_CONCAT(x, CHAR(10))
                FROM (
                    SELECT c2.label || '. ' || c2.text AS x
                    FROM choices c2
                    WHERE c2.question_id = q.id
                    ORDER BY c2.label
                )
            ) AS choices_text,
            (
                SELECT GROUP_CONCAT(c3.label, ', ')
                FROM choices c3
                WHERE c3.question_id = q.id
                  AND c3.is_correct = 1
                ORDER BY c3.label
            ) AS correct_letters,
            (
                SELECT GROUP_CONCAT(x, CHAR(10))
                FROM (
                    SELECT c4.label || '. ' || c4.text AS x
                    FROM choices c4
                    WHERE c4.question_id = q.id
                      AND c4.is_correct = 1
                    ORDER BY c4.label
                )
            ) AS correct_text,
            qu.title AS quiz_title
        FROM missed_questions mq
        JOIN questions q ON q.id = mq.question_id
        JOIN attempts a ON a.id = mq.attempt_id
        JOIN quizzes qu ON qu.id = a.quiz_id
        WHERE mq.attempt_id = ?
          AND mq.attempt_question_number IN ({q_marks})
        ORDER BY mq.attempt_question_number
        """,
        [attempt_id, *attempt_qnums],
    )

    rows = cur.fetchall()
    conn.close()

    logger.info("[ANKI-TSV] Missed TSV rows fetched: %s | attempt_id=%s",
                len(rows), attempt_id)

    # TSV header required by Anki
    lines = ["Front\tBack\tTags"]

    for idx, r in enumerate(rows, start=1):
        if not r["question_text"]:
            logger.warning("[ANKI-TSV] Empty question_text | row=%s", idx)

        # ---------- FRONT ----------
        front_parts = [r["question_text"] or ""]
        if r["choices_text"]:
            front_parts.extend(["", r["choices_text"]])

        front = "\n".join(front_parts).replace("\t", " ")

        # ---------- BACK ----------
        back_parts = []
        if r["correct_letters"]:
            back_parts.append(f"Correct: {r['correct_letters']}")
        if r["correct_text"]:
            back_parts.append(r["correct_text"])

        back = "\n".join(back_parts).replace("\t", " ")

        # ---------- TAGS ----------
        quiz_tag = (r["quiz_title"] or "autoquiz").replace(" ", "_")
        tags = f"{quiz_tag} missed"

        lines.append(f"{front}\t{back}\t{tags}")

        if idx == 1:
            logger.debug("[ANKI-TSV] First card preview:\nFRONT:\n%s\nBACK:\n%s",
                         front[:500], back[:500])

    tsv = "\n".join(lines)

    logger.info("[ANKI-TSV] TSV generated | lines=%s | bytes=%s",
                len(lines), len(tsv.encode("utf-8")))

    return Response(
        tsv,
        mimetype="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=missed_questions_anki.tsv"
        }
    )




# Legacy endpoint intentionally disabled.
# Review data is now served exclusively via /api/attempts.
# Kept as a placeholder to prevent accidental reintroduction.

# @app.route("/api/missed_questions")
# def api_missed_questions():
#     return {"error": "Deprecated endpoint. Use /api/attempts."}, 410











@app.route("/api/clear_db_history", methods=["POST"])
def clear_db_history():
    try:
        conn = get_db()
        cur = conn.cursor()

        # Respect foreign keys
        cur.execute("PRAGMA foreign_keys = ON")

        # Delete dependent rows first
        cur.execute("DELETE FROM missed_questions")
        cur.execute("DELETE FROM attempts")

        conn.commit()
        conn.close()

        return {"status": "ok", "message": "Persistent history cleared"}

    except Exception as e:
        print("DB CLEAR ERROR:", e)
        return {"status": "error"}, 500

@app.route("/api/portal_config")
def api_portal_config():
    try:
        cfg = load_portal_config()
        return jsonify(cfg)
    except Exception as e:
        print("portal_config API error:", e)
        return jsonify({"error": "failed"}), 500






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
        choices = re.findall(r"^[A-Z][\.\)]", b, flags=re.MULTILINE)
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
        dprint("[PARSE]", text)
    PARSE_LOG.append(text)


def parse_questions(source):
    import re, os

    global PARSE_LOG
    PARSE_LOG.clear()
    dbg("=== NEW PARSE SESSION STARTED ===")

    # Allow BOTH: file paths OR already-loaded quiz text
    if isinstance(source, str) and os.path.isfile(source):
        dbg("Input detected as FILE path → reading file")
        with open(source, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
    else:
        dbg("Input detected as RAW TEXT → using directly")
        raw = source

    # Normalize newlines
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Remove UTF-8 BOM if present
    text = text.lstrip("\ufeff")
    dbg("BOM stripped (if present)")

    # Split into question blocks
    blocks = re.split(
        r"(?=^\s*(?:Question\s*#?\s*\d+|\d+\s*[.) ]))",
        text,
        flags=re.IGNORECASE | re.MULTILINE
    )

    dbg("Total detected blocks:", len(blocks))

    questions = []
    fallback_number = 1

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

        qnum_match = re.match(
            r'^\s*(?:Question\s*#?\s*(\d+)|(\d+)\s*[.)])',
            lines[0],
            re.IGNORECASE
        )

        source_number = None
        if qnum_match:
            source_number = int(qnum_match.group(1) or qnum_match.group(2))

        q_number = source_number if source_number is not None else fallback_number

        dbg(f"\n--- Parsing Question Candidate #{q_number} ---")
        dbg(lines[0])

        q_lines = []
        raw_choices = []
        correct_letters = []
        choices_started = False

        for line in lines:
            lower = line.lower()

            # -------- Detect Choices --------
            mchoice = re.match(r"^\s*([A-Za-z])[\.\)]\s+(.*)", line)
            if mchoice:
                label = mchoice.group(1).upper()
                text_choice = mchoice.group(2).strip()
                dbg(f"Choice detected: {label} → {text_choice}")
                choices_started = True

                raw_choices.append({
                    "label": label,
                    "text": text_choice
                })
                continue

            # -------- Detect Correct Answer --------
            if "correct answer" in lower or "suggested answer" in lower:
                dbg("Found answer line:", line)

                m = re.search(r"[:\-]\s*([A-Za-z]+)", line)
                if m:
                    ans = re.sub(r"[^A-Za-z]", "", m.group(1)).upper()
                    if ans:
                        correct_letters = list(dict.fromkeys(list(ans)))
                        dbg("Parsed correct letters:", correct_letters)
                continue

            # -------- Question Text --------
            if not choices_started:
                if not (
                    lower.startswith("correct answer")
                    or lower.startswith("suggested answer")
                ):
                    q_lines.append(line)

        # ================================
        # VALIDATION
        # ================================
        if not correct_letters:
            dbg("!! Skipped: NO correct answer found")
            dbg(original_block[:200])
            continue

        if len(raw_choices) < 2:
            dbg("!! Skipped: Not enough choices:", raw_choices)
            continue

        # Build question text
        question_text = " ".join(q_lines)
        question_text = re.sub(
            r'^(?:Question\s*#?\s*\d+[\).\s-]*|\d+[\).\s-]*)\s*',
            '',
            question_text,
            flags=re.IGNORECASE
        ).strip()

        # ================================
        # FINALIZE CHOICES (ADD is_correct)
        # ================================
        choices = []
        for c in raw_choices:
            choices.append({
                "label": c["label"],
                "text": c["text"],
                "is_correct": c["label"] in correct_letters
            })

        dbg("Final Question Built:", question_text[:150])

        questions.append({
            "number": q_number,
            "question": question_text,
            "choices": choices,
            "correct": correct_letters
        })

        dbg("✓ Question Accepted\n")
        fallback_number += 1

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
        # Detect ANY lettered choices A–Z
        has_choice = any(re.match(r"^[A-Za-z][\.\)]\s+", l) for l in lines)

        has_answer_line = any(
            ("correct answer" in l.lower()) or ("suggested answer" in l.lower())
            for l in lines
        )
        num_choices = sum(
            1 for l in lines if re.match(r"^[A-Za-z][\.\)]\s+", l)

        )

        score = 0
        reason = []

        if has_choice:
            score += 1
            reason.append("Found A–Z answer choices")
        else:
            reason.append("No A–Z answer choices found")

        if has_answer_line:
            score += 1
            reason.append("Found 'Correct/Suggested Answer' line")
        else:
            reason.append("No explicit correct-answer line found")

        if num_choices >= 2:

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
<link rel="stylesheet" href="/static/style.css">

<!-- 🔑 Canonical quiz identity for script.js + DB -->
<script>
  window.quiz_title = "{quiz_title}";
</script>

</head>

<body>

<!-- 🔹 Load background dynamically -->
<script>
fetch("/config/portal.json")
  .then(r => r.json())
  .then(cfg => {{
      if (cfg.background_image) {{
          document.documentElement.style.setProperty(
              "--portal-bg",
              `url(${{cfg.background_image}})`
          );
      }}
  }});
</script>

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

            <!-- TOP BAR -->
            <div class="top-bar">

                <!-- LEFT -->
                <div class="top-left">
                    <button onclick="submitQuiz()" id="submitBtn" class="danger">
                        Submit Exam
                    </button>
                </div>

                <!-- RIGHT -->
                <div id="timer" class="hidden timerBox top-right">
                    <b>Time Remaining:</b>
                    <span id="timeDisplay">--:--</span>
                    <button id="pauseBtn" onclick="pauseExam()">Pause</button>
                </div>

            </div>

            <div id="qHeader"></div>
            <div id="qText"></div>
            <div id="choices"></div>

            <div class="controls">
                <button onclick="prev()">Prev</button>
                <button onclick="next()">Next</button>
            </div>
        </div>

        <div id="result" class="hidden"></div>

        <br>
        <button onclick="location.href='/'">🏠 Return To Portal</button>
        <button onclick="location.href='/library'">📚 Return To Quiz Library</button>

<!-- 🔹 Tell script.js which JSON file to load -->
<script>
  const QUIZ_FILE = "/data/{jsonfile}";
</script>

<script src="/script.js"></script>

</body>
</html>
"""

    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)




# =========================
# DATABASE CONFIG
# =========================



def get_or_create_question(conn, quiz_id, q):
    """
    Returns canonical question_id for a question.
    Creates it if it does not already exist.
    Matches the ACTUAL questions table schema.
    """
    cur = conn.cursor()

    number = q.get("number")
    text = q.get("question")

   # Look up / define canonical question values
    question_number = q.get("number")
    question_text = q.get("question") or q.get("text") or ""

    cur.execute(
        """
        INSERT INTO questions (
            quiz_id,
            question_number,
            question_text
        )
        VALUES (?, ?, ?)
        """,
        (quiz_id, question_number, question_text),
    )



    row = cur.fetchone()
    if row:
        return row[0]

    # Insert canonical question (schema-aligned)
    cur.execute("""
        INSERT INTO questions (
            quiz_id,
            number,
            text
        ) VALUES (?, ?, ?)
    """, (
        quiz_id,
        number,
        text
    ))

    question_id = cur.lastrowid

    # ---------- INSERT CHOICES ----------
    for c in choices:
        cur.execute("""
            INSERT INTO choices (
                question_id,
                label,
                text,
                is_correct
            ) VALUES (?, ?, ?, ?)
        """, (
            question_id,
            c["label"],
            c["text"],
            1 if c.get("is_correct") else 0
        ))

    conn.commit()
    return question_id







# =========================
# DATABASE HELPERS
# =========================
def get_db():
    dprint(f"[DB] get_db using DB_PATH = {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



def db_execute(query, params=()):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("DB ERROR:", e)
        return False


@app.route("/history_db")
def history_db():
    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ Pull all attempts with quiz name
    cur.execute("""
        SELECT 
            a.id,
            q.title AS quiz_title,
            a.score,
            a.total,
            a.percent,
            a.mode,
            a.started_at,
            a.completed_at,
            a.time_remaining
        FROM attempts a
        LEFT JOIN quizzes q ON a.quiz_id = q.id
        ORDER BY a.completed_at DESC
    """)
    attempts = cur.fetchall()

    results = []

    for row in attempts:
        attempt_id = row["id"]

        # 2️⃣ Pull missed questions for this attempt
        cur.execute("""
            SELECT
                question_number,
                question_text,
                correct_letters,
                correct_text,
                selected_letters,
                selected_text
            FROM missed_questions
            WHERE attempt_id = ?
        """, (attempt_id,))

        missed = [dict(m) for m in cur.fetchall()]

        results.append({
            "id": row["id"],
            "quiz_title": row["quiz_title"] or "Unknown Quiz",
            "score": row["score"],
            "total": row["total"],
            "percent": row["percent"],
            "mode": row["mode"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "time_remaining": row["time_remaining"],
            "missed": missed
        })

    conn.close()
    return jsonify(results)


# @app.route("/export/anki", methods=["POST"])
# def export_anki():
#     data = request.json or {}
#     attempt_ids = data.get("attempt_ids", [])

#     if not attempt_ids:
#         return jsonify({"error": "No attempts selected"}), 400

#     # 1️⃣ Pull attempts from DB
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     cur = conn.cursor()

#     placeholders = ",".join("?" for _ in attempt_ids)
#     cur.execute(
#         f"SELECT * FROM attempts WHERE id IN ({placeholders})",
#         attempt_ids
#     )

#     rows = cur.fetchall()
#     conn.close()

#     if not rows:
#         return jsonify({"error": "No attempts found"}), 404

#     # 2️⃣ Extract missed questions
#     questions = []

#     for row in rows:
#         missed = json.loads(row["missedQuestions"] or "[]")

#         for m in missed:
#             questions.append({
#                 "question": m.get("question", ""),
#                 "choices": m.get("allChoices", []),
#                 "correct": m.get("correctText", []),
#                 "selected": m.get("selectedText", []),
#                 "quiz_title": row["quiz_title"],
#                 "attempt_id": row["id"],
#             })

#     if not questions:
#         return jsonify({"error": "No missed questions to export"}), 400

#     # 3️⃣ Generate deck
#     from anki_deck import build_anki_deck

#     filename = build_anki_deck(
#         questions=questions,
#         deck_name="Missed Questions"
#     )

#     return send_from_directory(
#         directory=os.path.dirname(filename),
#         path=os.path.basename(filename),
#         as_attachment=True
#     )





# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=9001,
        debug=False,
        use_reloader=False
    )

