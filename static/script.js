/* =====================================================
   GLOBAL STATE
===================================================== */
let quiz = [];
let index = 0;
let examMode = false;
let userAnswers = {};
let paused = false;
let examTimer = null;
let timeRemaining = 90 * 60; // 90 minutes
let examStartTime = null;
let examStartedAt = null;



/* =====================================================
   SAFELY RELOCATE SUBMIT BUTTON (OLD QUIZZES → NEW UI)
===================================================== */
document.addEventListener("DOMContentLoaded", () => {
    // Find submit button
    const submitBtn = document.getElementById("submitBtn");
    if (!submitBtn) return;   // nothing to do

    // Find top-left bar target
    const topLeft = document.querySelector(".top-left");
    if (!topLeft) return;     // quiz HTML doesn't support it → do nothing

    // If it's already in top-left, leave it alone
    if (submitBtn.parentElement === topLeft) return;

    console.log("Relocating Submit Exam button to top-left...");
    topLeft.appendChild(submitBtn);
});





/* =====================================================
   LOAD QUIZ JSON
===================================================== */
async function loadQuiz() {
    try {
        const file = (typeof QUIZ_FILE !== "undefined") ? QUIZ_FILE : "quiz.json";
        console.log("Loading quiz:", file);
        const res = await fetch(file);
        if (!res.ok) throw new Error("HTTP " + res.status);
        quiz = await res.json();
        console.log("Quiz loaded. Questions:", quiz.length);
    } catch (err) {
        console.error("Failed to load quiz:", err);
        alert("Failed to load quiz questions.");
    }
}
loadQuiz();

/* =====================================================
   UI UPGRADE — Create Top Bar + Move Submit + Timer
   Works for OLD quizzes only.
   If new layout already exists → does nothing.
===================================================== */
document.addEventListener("DOMContentLoaded", () => {

    // If new top-bar already exists (new quizzes), do nothing
    if (document.querySelector(".top-bar")) {
        console.log("Top bar already exists — layout OK");
        return;
    }

    const quizDiv = document.getElementById("quiz");
    const progress = document.getElementById("progressBarOuter");
    const timer = document.getElementById("timer");
    const controls = document.querySelector(".controls");

    // Fail-safe: if we can't find required elements, do nothing
    if (!quizDiv || !progress || !timer || !controls) {
        console.warn("Top bar patch skipped — layout elements missing");
        return;
    }

    // Find submit button
    const submitBtn =
        document.getElementById("submitBtn") ||
        document.querySelector("button[onclick='submitQuiz()']");

    if (!submitBtn) {
        console.warn("Submit button not found — skipping patch");
        return;
    }

    console.log("Applying TOP BAR UI upgrade...");

    // Create top bar containers
    const topBar = document.createElement("div");
    topBar.className = "top-bar";

    const left = document.createElement("div");
    left.className = "top-left";

    const right = document.createElement("div");
    right.className = "top-right";

    // Move submit into left
    left.appendChild(submitBtn);

    // Move timer into right
    right.appendChild(timer);

    // Assemble bar
    topBar.appendChild(left);
    topBar.appendChild(right);

    // Insert bar RIGHT AFTER progress bar
    progress.insertAdjacentElement("afterend", topBar);
});



/* =====================================================
   RENDER QUESTION
===================================================== */
function renderQuestion() {
    if (!quiz.length) return;

    const q = quiz[index];
    const key = `q${index}`;
    const selected = userAnswers[key] || [];

    const headerEl = document.getElementById("qHeader");
    const textEl = document.getElementById("qText");
    const choicesEl = document.getElementById("choices");

    if (headerEl) {
        headerEl.innerText = `Question ${index + 1} of ${quiz.length}`;
    }
    if (textEl) {
        textEl.innerText = q.question || "";
    }

    if (!choicesEl) return;

    let html = "";
    q.choices.forEach((choice, i) => {
        const label = choice.label;
        const choiceText = choice.text;
        let cls = "choice";


// Only visually “select” answers in EXAM MODE
if (examMode && selected.includes(i)) {
    cls += " selected";
}


        html += `
            <div 
                class="${cls}"
                data-index="${i}"
                onclick="selectChoice(${i})">
                <b>${label}.</b> ${choiceText}
            </div>
        `;
    });

    choicesEl.innerHTML = html;

    // Study mode: immediately show correct/incorrect colors
   if (!examMode && selected.length > 0) {
    applyStudyFeedback();
}


    updateProgressBar();
    updateNavButtons();
    updatePauseButtonUI();
    updateTimerLabelUI();
    updateStudyModeBadge();
}

/* =====================================================
   SELECT CHOICE
===================================================== */
function selectChoice(i) {
    if (!quiz.length) return;

    const q = quiz[index];
    const key = `q${index}`;

    const isMulti = Array.isArray(q.correct) && q.correct.length > 1;
    let arr = userAnswers[key] || [];

    // --- STUDY MODE ---
    if (!examMode) {

        if (!isMulti) {
            // single-answer question → normal behavior
            arr = [i];
        } else {
            // MULTI-ANSWER STUDY MODE → toggle selections
            if (arr.includes(i)) {
                arr = arr.filter(v => v !== i);
            } else {
                arr.push(i);
                arr.sort();
            }
        }

        userAnswers[key] = arr;
        applyStudyFeedback();
        renderQuestion();
        return;
    }

    // --- EXAM MODE ---
    if (!isMulti) {
        arr = [i];
    } else {
        if (arr.includes(i)) {
            arr = arr.filter(v => v !== i);
        } else {
            arr.push(i);
            arr.sort();
        }
    }

    userAnswers[key] = arr;
    renderQuestion();
}



/* =====================================================
   NAVIGATION
===================================================== */
function next() {
    if (!quiz.length) return;
    if (index < quiz.length - 1) {
        index++;
        renderQuestion();
    }
}

function prev() {
    if (!quiz.length) return;
    if (index > 0) {
        index--;
        renderQuestion();
    }
}

/* =====================================================
   NAV BUTTON VISIBILITY (HIDE NEXT ON LAST QUESTION)
===================================================== */
function updateNavButtons() {
    // Try common ways to find the buttons (works across old/new quiz HTML)
    const buttons = Array.from(document.querySelectorAll("button"));

    const nextBtn =
        document.getElementById("nextBtn") ||
        buttons.find(b => (b.getAttribute("onclick") || "").includes("next(")) ||
        buttons.find(b => (b.textContent || "").trim().toLowerCase() === "next") ||
        buttons.find(b => (b.textContent || "").toLowerCase().includes("next"));

    const prevBtn =
        document.getElementById("prevBtn") ||
        buttons.find(b => (b.getAttribute("onclick") || "").includes("prev(")) ||
        buttons.find(b => (b.textContent || "").trim().toLowerCase() === "prev") ||
        buttons.find(b => (b.textContent || "").toLowerCase().includes("prev"));

    // If we can't find the buttons on this quiz HTML, do nothing safely
    if (!quiz.length) return;

    // Prev disabled on first question (nice UX; safe)
    if (prevBtn) prevBtn.disabled = (index === 0);

    // Hide Next on last question; show otherwise
    if (nextBtn) {
        const isLast = (index === quiz.length - 1);
        nextBtn.style.display = isLast ? "none" : "inline-block";
    }
}

/* =====================================================
   STUDY MODE UI VISIBILITY
===================================================== */
function updateStudyModeUI() {
    const timer = document.getElementById("timer");
    const pauseBtn =
        document.getElementById("pauseBtn") ||
        document.querySelector("button[onclick='pauseQuiz()']");

    if (!examMode) {
        // Study mode → hide timer + pause
        if (timer) timer.style.display = "none";
        if (pauseBtn) pauseBtn.style.display = "none";
    } else {
        // Exam mode → restore
        if (timer) timer.style.display = "";
        if (pauseBtn) pauseBtn.style.display = "";
    }
}


/* =====================================================
   PAUSE BUTTON VISIBILITY
===================================================== */
function updatePauseButtonUI() {
    const pauseBtn =
        document.getElementById("pauseBtn") ||
        document.querySelector("button[onclick='pauseQuiz()']");

    if (!pauseBtn) return;

    // Study mode → hide pause
    pauseBtn.style.display = examMode ? "inline-block" : "none";
}


/* =====================================================
   TIMER LABEL VISIBILITY
===================================================== */
function updateTimerLabelUI() {
    const timerLabel = document.querySelector(
        "#timer, .timer, .time-remaining, #timeRemaining"
    );

    if (!timerLabel) return;

    timerLabel.style.display = examMode ? "" : "none";
}


/* =====================================================
   STUDY MODE BADGE
===================================================== */
function updateStudyModeBadge() {
    let badge = document.getElementById("studyModeBadge");

    if (!examMode) {
        if (!badge) {
            badge = document.createElement("div");
            badge.id = "studyModeBadge";
            badge.innerHTML = `
                <div style="font-size:16px;font-weight:600;letter-spacing:.3px">
                    📘 Study Mode
                </div>
                <div style="font-size:12px;opacity:.9;margin-top:2px">
                    Learn at your own pace
                </div>
            `;

            badge.style.padding = "10px 14px";
            badge.style.borderRadius = "8px";
            badge.style.background = "rgba(255,255,255,0.15)";
            badge.style.border = "1px solid rgba(255,255,255,0.25)";
            badge.style.textAlign = "center";
            badge.style.boxShadow = "0 0 10px rgba(0,0,0,.35)";


            const timer = document.getElementById("timer");
            if (timer && timer.parentNode) {
                timer.parentNode.insertBefore(badge, timer.nextSibling);
            }
        }
        badge.style.display = "block";
    } else {
        if (badge) badge.style.display = "none";
    }
}



/* =====================================================
   STUDY-MODE FEEDBACK
===================================================== */
function applyStudyFeedback() {
    if (!quiz.length) return;

    const q = quiz[index];
    if (!q.correct || !Array.isArray(q.correct)) return;

    const key = `q${index}`;
    const selected = userAnswers[key] || [];

    const correctIndexes = q.correct.map(letter =>
        String(letter).toUpperCase().charCodeAt(0) - 65
    );

    const buttons = document.querySelectorAll("#choices .choice");

    // Clear previous feedback
    buttons.forEach(btn => {
        btn.classList.remove("correct-choice", "wrong-choice");
    });

    // Mark ONLY what the user picked
    selected.forEach(idx => {
        if (!buttons[idx]) return;

        if (correctIndexes.includes(idx)) {
            buttons[idx].classList.add("correct-choice");   // green
        } else {
            buttons[idx].classList.add("wrong-choice");     // red
        }
    });
}




/* =====================================================
   PROGRESS BAR
===================================================== */
function updateProgressBar() {
    const bar = document.getElementById("progressBarInner");
    if (!bar || !quiz.length) return;

    const pct = ((index + 1) / quiz.length) * 100;
    bar.style.width = pct + "%";
}

/* =====================================================
   START QUIZ (Study or Exam)
===================================================== */
function startQuiz(isExam) {
    examMode = isExam;
    index = 0;
    userAnswers = {};

    if (examMode) {
    examStartTime = new Date().toISOString();
    } else {
        examStartTime = null;
    }



    console.log("START QUIZ. examMode =", examMode);

    // Show Submit ONLY in Exam Mode
    const submitBtn = document.querySelector("button[onclick='submitQuiz()']");
    if (submitBtn) submitBtn.style.display = examMode ? "inline-block" : "none";

    const modeSelect = document.getElementById("modeSelect");
    const quizDiv = document.getElementById("quiz");
    const resultDiv = document.getElementById("result");
    const timerDiv = document.getElementById("timer");

    if (modeSelect) modeSelect.classList.add("hidden");
    if (quizDiv) quizDiv.classList.remove("hidden");
    if (resultDiv) {
        resultDiv.classList.add("hidden");
        resultDiv.style.display = "none";
    }

    updatePauseButtonUI(); // 👈 ADD THIS LINE EXACTLY HERE
    updateTimerLabelUI();
    updateStudyModeBadge();

    // Reset pause overlay / blur
    const overlay = document.getElementById("pauseOverlay");
    if (overlay) overlay.classList.remove("show");
    document.body.classList.remove("blurred");
    paused = false;

    // In Study mode: no timer
    if (!examMode) {
        if (timerDiv) timerDiv.classList.add("hidden");
        stopExamTimer();
    } else {
        // Exam mode: show timer + start fresh 90-min countdown
        if (timerDiv) timerDiv.classList.remove("hidden");
        timeRemaining = 90 * 60;
        startExamTimer();
    }
    // NEW: record start time
    examStartTime = new Date().toISOString();


    renderQuestion();
}


/* =====================================================
   EXAM TIMER + PAUSE / RESUME
===================================================== */
function startExamTimer() {
    console.log("TIMER START");
    const display = document.getElementById("timeDisplay");

    if (examTimer) {
        clearInterval(examTimer);
        examTimer = null;
    }

    examTimer = setInterval(() => {
        if (paused) return;

        timeRemaining--;

        const m = Math.floor(timeRemaining / 60);
        const s = timeRemaining % 60;

        if (display) {
            display.innerText = `${m}:${s.toString().padStart(2, "0")}`;
        }

        if (timeRemaining <= 0) {
            clearInterval(examTimer);
            examTimer = null;
            submitQuiz(true);

        }
    }, 1000);
}

function pauseExam() {
    if (!examMode) return;
    console.log("PAUSE CLICKED");

    paused = true;

    const overlay = document.getElementById("pauseOverlay");
    if (overlay) {
        overlay.classList.add("show");
        console.log("Overlay class after pause:", overlay.className);
    }

    document.body.classList.add("blurred");
}

function resumeExam() {
    if (!examMode) return;
    console.log("RESUME CLICKED");

    paused = false;

    const overlay = document.getElementById("pauseOverlay");
    if (overlay) {
        overlay.classList.remove("show");
    }

    document.body.classList.remove("blurred");
}

function stopExamTimer() {
    if (examTimer) {
        clearInterval(examTimer);
        examTimer = null;
    }
}

/* =====================================================
   SUBMIT — EXAM ONLY
===================================================== */
/* =====================================================
   SUBMIT — EXAM ONLY
===================================================== */
function submitQuiz(force = false) {

    // Do nothing in Study Mode
    if (!examMode) {
        console.log("submitQuiz called but examMode = false; ignoring.");
        return;
    }

    // Manual submit confirmation
    if (!force) {
        const ok = confirm("Are you sure you want to submit your exam?");
        if (!ok) {
            console.log("User cancelled exam submission.");
            return;
        }
    }


    console.log("SUBMIT EXAM");

    if (!quiz || !Array.isArray(quiz) || quiz.length === 0) {
        console.error("Quiz is empty or not loaded.");
        alert("Quiz failed to load.");
        return;
    }

    let correct = 0;
    let missed = [];
    let answerDetails = [];

    console.log("QUESTIONS:", quiz.length);

    try {
        for (let i = 0; i < quiz.length; i++) {
            const q = quiz[i];

            if (!q || !q.correct) {
                console.warn("Question missing 'correct' field:", q);
                continue;
            }

            const key = `q${i}`;
            let ans = userAnswers[key];

            // Normalize answer to an array of indexes
            if (!Array.isArray(ans)) {
                ans = (ans === undefined || ans === null) ? [] : [ans];
            }

            // Convert ["A"] -> [0], ["D"] -> [3], etc.
            const correctIndexes = q.correct.map(
                l => String(l).toUpperCase().charCodeAt(0) - 65
            );

            // Compare arrays safely
            const isCorrect =
                ans.length === correctIndexes.length &&
                ans.every((v, idx) => v === correctIndexes[idx]);

            if (isCorrect) {
                correct++;
            } else {
    missed.push({
        attemptQuestionNumber: i + 1,
        number: q.number || (i + 1),
        question: q.question,

        // 🔑 FULL SNAPSHOT OF ALL CHOICES (THIS IS THE FIX)
        choices: q.choices.map(c => ({
            label: c.label,
            text: c.text
        })),

        // Correct Answers
        correctLetters: q.correct,
        correctText: q.correct.map(letter => {
            const choice = q.choices.find(
                c => c.label.toUpperCase() === letter.toUpperCase()
            );

            if (!choice) {
                console.error(
                    "SCORING ERROR: Missing choice for letter",
                    letter,
                    "Question:",
                    q
                );
                return `${letter} — [Missing choice]`;
            }

            return `${letter} — ${choice.text}`;
        }),

        // What the user actually selected
        selectedIndexes: ans,
        selectedLetters: ans.map(idx => String.fromCharCode(65 + idx)),
        selectedText: ans.map(idx =>
            `${String.fromCharCode(65 + idx)} — ${q.choices[idx].text}`
        )
    });

}

        }
    } catch (e) {
        console.error("ERROR DURING SCORING:", e);
        alert("Something went wrong while scoring the exam.");
        return;
    }

    console.log("SCORING COMPLETE. Correct:", correct);

    const total = quiz.length;
    const percent = Math.round((correct / total) * 100);

    stopExamTimer();

    const attemptId = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : String(Date.now());

    // Save history for dashboard/history.html
    saveHistory(percent, correct, total, missed, attemptId);


    // =========================
    // ALSO SAVE TO SERVER DB
    // (safe: if it fails nothing breaks)
    // =========================
    fetch("/record_attempt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            quizTitle: window.quiz_title || QUIZ_FILE || "Unknown Quiz",
            quizId: window.QUIZ_ID,

            score: correct,
            total: total,
            percent: percent,
            attemptId: attemptId,
            startedAt: examStartTime,
            completedAt: new Date().toISOString(),
            timeRemaining: timeRemaining,

            mode: "Exam",

            missedDetails: missed
        })

    })
    .then(res => res.json().catch(() => ({})))
    .then(data => console.log("DB save response:", data))
    .catch(err => console.warn("DB save failed (but app is fine):", err));



    // existing code continues normally after this
    const quizDiv = document.getElementById("quiz");
    const resultDiv = document.getElementById("result");


    if (quizDiv) quizDiv.classList.add("hidden");

    if (resultDiv) {
        resultDiv.classList.remove("hidden");
        resultDiv.style.display = "block";

        resultDiv.innerHTML = `
            <h2>Exam Results</h2>
            <p><b>Score:</b> ${correct} / ${total} (${percent}%)</p>

            <button onclick="location.href='/history?attempt=${attemptId}'">
                📌 Review This Attempt
            </button>

            <button onclick="location.href='/history'">
                📜 View Full History
            </button>


            <button onclick="location.reload()">
                🔁 Retake Exam
            </button>

            <button onclick="location.href='/'">
                🏠 Return to Portal
            </button>
        `;
    }

    console.log("RESULT UI RENDERED. Attempt ID:", attemptId);
}


/* =====================================================
   SAVE HISTORY (localStorage, per-quiz)
===================================================== */
/* =====================================================
   SAVE HISTORY (localStorage, per-quiz)
===================================================== */
function saveHistory(percent, correct, total, missed, attemptId) {
    const HISTORY_KEY = "serverplus_history_v2";

    let store;
    try {
        store = JSON.parse(localStorage.getItem(HISTORY_KEY) || "{}");
    } catch (e) {
        console.warn("Failed to parse history store, resetting.", e);
        store = {};
    }

    /* --------------------------------------------
       Determine Quiz KEY for grouping history
       Priority:
       1️⃣ User-supplied quiz name (from your portal)
       2️⃣ Existing QUIZ_FILE fallback (old behavior)
    -------------------------------------------- */
    let quizKey = "Unnamed Quiz";

    // If you already store quiz title globally, catch it
    if (window.quiz_title && window.quiz_title.trim()) {
        quizKey = window.quiz_title.trim();
    }

    // If you capture quiz name from an input box
    else if (document.getElementById("quiz_title")) {
        const val = document.getElementById("quiz_title").value.trim();
        if (val) quizKey = val;
    }

    // FINAL fallback to filename (keeps compatibility)
    else if (typeof QUIZ_FILE !== "undefined") {
        quizKey = QUIZ_FILE;
    }

    if (!store[quizKey]) {
        store[quizKey] = [];
    }

    store[quizKey].push({
        id: attemptId,
        date: new Date().toLocaleString(),
        score: correct,      
        total: total,        
        percent: percent,    
        timeRemaining: timeRemaining,
        mode: "Exam",
        missed: missed       
    });

    localStorage.setItem(HISTORY_KEY, JSON.stringify(store));
    console.log("History saved for quizKey:", quizKey, "Attempt:", attemptId);
}

function resetDatabase() {
    const msg =
        "⚠️ WARNING ⚠️\n\n" +
        "This will permanently delete:\n" +
        "• ALL quizzes\n" +
        "• ALL attempts\n" +
        "• ALL missed-question history\n\n" +
        "Quiz numbering will restart from the beginning.\n\n" +
        "This action CANNOT be undone.\n\n" +
        "Click OK to continue.";

    if (!confirm(msg)) {
        return;
    }

    fetch("/wipe_database", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error("Database reset failed");
        }
        return res.json();
    })
    .then(() => {
        alert("Database reset complete.");
        window.location.reload();
    })
    .catch(err => {
        console.error(err);
        alert("Error resetting database. See console.");
    });
}

