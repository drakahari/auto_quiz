from flask import Flask, send_from_directory, request, redirect, render_template_string, jsonify
import os, re, json, time, sqlite3

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
DB_PATH = os.path.join(BASE_DIR, "results.db")



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

                <!-- ========================= -->
                <!--  REGEX REPLACE SECTION    -->
                <!-- ========================= -->
                <h3>Optional: Regex Replace Rules</h3>
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

                <!-- ========================= -->
                <!--  REGEX PRESET CHECKBOXES  -->
                <!-- ========================= -->
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

    # =========================
    # APPLY STRIP RULES (optional regex mode)
    # =========================
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

        <!-- STEP 7: PRE-PROCESS SUMMARY PANEL -->
        <div style="background:#1a1a1a; padding:12px; border-radius:8px; margin-bottom:18px;">
            <h2>🧪 Pre-Processing Summary</h2>

            <p><b>Regex Strip Mode:</b>
                {% if regex_mode %}
                    Enabled ✔
                {% else %}
                    Disabled ❌
                {% endif %}
            </p>

            {% if strip_rules %}
            <h3>Lines Removed By Strip Rules</h3>
            <ul>
                {% for r in strip_rules %}
                <li>{{r}}</li>
                {% endfor %}
            </ul>
            {% else %}
            <p>No strip rules applied.</p>
            {% endif %}

            <!-- MANUAL REGEX -->
            {% if replace_rules %}
            <h3>Manual Regex Replace Rules</h3>
            <ul>
                {% for r in replace_rules %}
                <li>{{r}}</li>
                {% endfor %}
            </ul>
            {% else %}
            <p>No manual regex replace rules entered.</p>
            {% endif %}

            <!-- PRESET STATES -->
            <h3>✨ Regex Presets</h3>
            <ul>
                <li>
                    Number Prefix Removal:
                    {% if preset_number_prefix_checked %}
                        Enabled ✔
                    {% else %}
                        Off ❌
                    {% endif %}
                </li>

                <li>
                    PDF Line Wrapping Fix:
                    {% if preset_pdf_spacing_checked %}
                        Enabled ✔
                    {% else %}
                        Off ❌
                    {% endif %}
                </li>

                <li>
                    Header/Footer Cleanup:
                    {% if preset_headers_checked %}
                        Enabled ✔
                    {% else %}
                        Off ❌
                    {% endif %}
                </li>
            </ul>

            <!-- RULES THAT ACTUALLY FIRED -->
            {% if applied_rules %}
            <h3>Rules That Actually Changed Text</h3>
            <ul>
                {% for r in applied_rules %}
                <li>✔ {{r}}</li>
                {% endfor %}
            </ul>
            {% else %}
            <p>No regex rules altered text.</p>
            {% endif %}

            <!-- INVISIBLE CLEAN -->
            <h3>Invisible Character Cleanup</h3>
            {% if invis_cleanup_enabled %}
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
            {% else %}
                <p>Invisible Character Cleanup: Disabled ❌</p>
            {% endif %}

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

        <h2>Text To Be Parsed</h2>
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
                Green = added · Red = removed · Yellow = changed
            </p>
        </div>

        <script>
        function toggleDiff() {
            const panel = document.getElementById("diffPanel");
            const show = panel.style.display === "none";
            if (show) runDiff();
            panel.style.display = show ? "block" : "none";
        }

        function runDiff() {
            const orig = document.getElementById("origBox").innerText.split("\\n");
            const clean = document.getElementById("cleanBox").innerText.split("\\n");

            let out = "";
            const max = Math.max(orig.length, clean.length);

            for (let i = 0; i < max; i++) {
                const o = orig[i] || "";
                const c = clean[i] || "";

                if (o === c) {
                    out += o + "\\n";
                } 
                else if (!c) {
                    out += "[REMOVED] " + o + "\\n";
                }
                else if (!o) {
                    out += "[ADDED] " + c + "\\n";
                }
                else {
                    out += "[CHANGED] " + o + "  →  " + c + "\\n";
                }
            }

            document.getElementById("diffView").innerText = out;
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
        temp_logo_name=temp_logo_name,
        regex_mode=regex_mode,
        strip_rules=strip_rules,
        replace_rules=replace_rules_raw.splitlines() if replace_rules_raw else [],
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

    # =========================
    # PARSE QUIZ
    # =========================
    quiz_data = parse_questions(path)

    # Always save a parse log so failures are debuggable
    ts_fail = int(time.time())
    log_filename = f"parse_log_{ts_fail}.txt"

    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

    # If no questions parsed, show failure UI + log link
    if not quiz_data:
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

    if not file or not file.filename.lower().endswith(".txt"):
        return "Only .txt files are supported.", 400

    quiz_title = request.form.get("quiz_title", "Generated Quiz")

    path = os.path.join(UPLOAD_FOLDER, "latest.txt")
    file.save(path)

    # Handle optional logo
    logo_file = request.files.get("quiz_logo")
    logo_filename = None
    if logo_file and logo_file.filename:
        ext = os.path.splitext(logo_file.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            ts = int(time.time())
            logo_filename = f"logo_{ts}{ext}"
            logo_file.save(os.path.join(LOGO_FOLDER, logo_filename))

    # =========================
    # READ FILE CONTENT
    # =========================
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # =========================
    # PARSE QUIZ (PASS TEXT!)
    # =========================
    quiz_data = parse_questions(text)

    print("UPLOAD MODE FINAL PARSE COUNT:", 
          0 if quiz_data is None else len(quiz_data))

    # Always save parse log
    ts_fail = int(time.time())
    log_filename = f"parse_log_{ts_fail}.txt"
    with open(os.path.join(DATA_FOLDER, log_filename), "w", encoding="utf-8") as f:
        f.write("\n".join(PARSE_LOG))

    if not quiz_data:
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
                <p>No valid questions were parsed.</p>
                <p>You can download the parser log:</p>

                <button onclick="location.href='/data/{{log_filename}}'">
                    📥 Download Parse Log
                </button>

                <br><br>
                <button onclick="location.href='/upload'">
                    ⬅ Back To Upload Page
                </button>
                <button onclick="location.href='/'">
                    🏠 Return To Portal
                </button>
            </div>
        </div>
        </body>
        </html>
        """, log_filename=log_filename), 400



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

    # Ensure safe defaults if missing from portal.json
    cfg.setdefault("show_confidence", True)
    cfg.setdefault("enable_regex_replace", False)
    cfg.setdefault("auto_bom_clean", False)
    cfg.setdefault("enable_show_invisibles", True)

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

            <br><br>

            <button type="submit">💾 Save Settings</button>
        </form>

        <br>
        <button onclick="location.href='/'">⬅ Back To Portal</button>

    </div>

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

    title = request.form.get("portal_title", cfg.get("title", "Training Portal")).strip()

    cfg["title"] = title
    cfg["show_confidence"] = ("show_confidence" in request.form)
    cfg["enable_regex_replace"] = ("enable_regex_replace" in request.form)

    # 🔥 Correct Key Name
    cfg["auto_bom_clean"] = ("auto_bom_clean" in request.form)

    # (optional future UI toggle, keep or remove)
    cfg["enable_show_invisibles"] = ("enable_show_invisibles" in request.form)

    with open(PORTAL_CONFIG, "w") as f:
        json.dump(cfg, f, indent=4)

    return redirect("/settings")



@app.route("/record_attempt", methods=["POST"])
def record_attempt():
    data = request.json
    print("📩 Incoming Attempt Payload:", json.dumps(data, indent=2))

    quiz_title = data.get("quizTitle")
    score = data.get("score")
    total = data.get("total")
    percent = data.get("percent")
    attempt_id = data.get("attemptId")

    # CamelCase coming from JS
    started_at = data.get("startedAt")
    completed_at = data.get("completedAt")
    time_remaining = data.get("timeRemaining")
    mode = data.get("mode", "Exam")

    print("Saving attempt to DB:", quiz_title, percent)

    conn = get_db()
    cur = conn.cursor()

    try:
        # 1️⃣ Ensure quiz exists
        cur.execute(
            "INSERT OR IGNORE INTO quizzes (title) VALUES (?)",
            (quiz_title,)
        )

        # 2️⃣ Lookup quiz_id
        cur.execute(
            "SELECT id FROM quizzes WHERE title = ? LIMIT 1",
            (quiz_title,)
        )
        row = cur.fetchone()

        if not row:
            raise Exception("Quiz lookup failed")
        quiz_id = row["id"]

        # 3️⃣ Insert Attempt
        cur.execute(
            """
            INSERT INTO attempts (
                id,
                quiz_id,
                started_at,
                completed_at,
                score,
                total,
                percent,
                time_remaining,
                mode
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                quiz_id,
                started_at,
                completed_at,
                score,
                total,
                percent,
                time_remaining,
                mode
            )
        )

        # 4️⃣ Store missed questions (if any)
        missed = data.get("missedDetails", [])

        for m in missed:
            cur.execute(
                """
                INSERT INTO missed_questions (
                    attempt_id,
                    question_number,
                    question_text,
                    correct_letters,
                    correct_text,
                    selected_letters,
                    selected_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    m.get("number"),
                    m.get("question"),
                    ",".join(m.get("correctLetters", [])),
                    "\n".join(m.get("correctText", [])),
                    ",".join(m.get("selectedLetters", [])),
                    "\n".join(m.get("selectedText", []))
                )
            )


        conn.commit()
        conn.close()
        return {"status": "ok"}

    except Exception as e:
        conn.rollback()
        conn.close()
        print("DB ERROR:", e)
        return {"status": "db_error"}, 500




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
                question_number,
                question_text,
                correct_letters,
                correct_text,
                selected_letters,
                selected_text
            FROM missed_questions
            WHERE attempt_id = ?
        """, (attempt["id"],))

        mq = cur.fetchall()

        attempt["missedQuestions"] = [
            {
                "number": m["question_number"],
                "question": m["question_text"],
                "correctLetters": (m["correct_letters"] or "").split(","),
                "correctText": (m["correct_text"] or "").split("\n"),
                "selectedLetters": (m["selected_letters"] or "").split(","),
                "selectedText": (m["selected_text"] or "").split("\n")
            }
            for m in mq
        ]

    conn.close()
    return jsonify({"attempts": attempts})










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
        print("[PARSE]", text)
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
            mchoice = re.match(r"^\s*([A-Za-z])[\.\)]\s+(.*)", line)

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

        # Build full question text
        question_text = " ".join(q_lines)

        # --- UX CLEANUP ---
        question_text = re.sub(
            r'^(?:Question\s*#?\s*\d+[\).\s-]*|\d+[\).\s-]*)\s*',
            '',
            question_text,
            flags=re.IGNORECASE
        )

        dbg("Final Question Built:", question_text[:150])

        questions.append({
            "number": number,
            "question": question_text,
            "choices": choices,
            "correct": correct
        })

        dbg("✓ Question Accepted\n")
        number += 1

    # ================================
    # END OF LOOP — FINALIZE
    # ================================
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

        <!-- TOP BAR: Submit (LEFT) — Timer & Pause (RIGHT) -->
        <div class="top-bar">

            <!-- LEFT SIDE -->
            <div class="top-left">
                <button onclick="submitQuiz()" id="submitBtn" class="danger">
                    Submit Exam
                </button>
            </div>

            <!-- RIGHT SIDE -->
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
            <!-- Submit Exam REMOVED from here -->
        </div>
    </div>

    <div id="result" class="hidden"></div>

    <br>
    <button onclick="location.href='/'">🏠 Return To Portal</button>
    <button onclick="location.href='/library'">📚 Return To Quiz Library</button>


<script>
  /* Make title available to script.js + DB saving */
  window.quiz_title = "{quiz_title}";

 /* This tells script.js which JSON file to load for this quiz */
  const QUIZ_FILE = "/data/{jsonfile}";
  window.quiz_title = "{quiz_title}";
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
DB_PATH = os.path.join(BASE_DIR, "results.db")


# =========================
# DATABASE HELPERS
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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




# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
