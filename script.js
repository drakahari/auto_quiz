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
    q.choices.forEach((choiceText, i) => {
        const label = String.fromCharCode(65 + i);
        let cls = "choice";
        if (selected.includes(i)) {
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
        applyStudyFeedback(selected[0]);
    }

    updateProgressBar();
}

/* =====================================================
   SELECT CHOICE
===================================================== */
function selectChoice(i) {
    if (!quiz.length) return;

    const key = `q${index}`;
    userAnswers[key] = [i];

    // Study mode: show correct/incorrect right away
    if (!examMode) {
        applyStudyFeedback(i);
    }

    // Re-render so "selected" class is applied in both modes
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
   STUDY-MODE FEEDBACK
===================================================== */
function applyStudyFeedback(selectedIndex) {
    if (!quiz.length) return;

    const q = quiz[index];

    if (!q.correct || !Array.isArray(q.correct)) return;

    // Convert ["A"] -> [0], ["B"] -> [1], etc.
    const correctIndexes = q.correct.map(letter =>
        String(letter).toUpperCase().charCodeAt(0) - 65
    );

    const buttons = document.querySelectorAll("#choices .choice");

    // Clear previous state
    buttons.forEach(btn => {
        btn.classList.remove("correct-choice", "wrong-choice");
    });

    // Mark all correct answers in green
    correctIndexes.forEach(idx => {
        if (buttons[idx]) {
            buttons[idx].classList.add("correct-choice");
        }
    });

    // If user chose a wrong one, mark it red
    if (!correctIndexes.includes(selectedIndex) && buttons[selectedIndex]) {
        buttons[selectedIndex].classList.add("wrong-choice");
    }
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

    console.log("START QUIZ. examMode =", examMode);

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
            submitQuiz();
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
function submitQuiz() {
    // Do nothing in Study Mode
    if (!examMode) {
        console.log("submitQuiz called but examMode = false; ignoring.");
        return;
    }

    console.log("SUBMIT EXAM");

    if (!quiz || !Array.isArray(quiz) || quiz.length === 0) {
        console.error("Quiz is empty or not loaded.");
        alert("Quiz failed to load.");
        return;
    }

    let correct = 0;
    let missed = [];

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
    number: q.number || (i + 1),
    question: q.question,

    // Letters like ["A","C"]
    correctLetters: q.correct,

    // Convert to readable text like:
    // "A — Encryption prevents access"
    correctText: q.correct.map(letter => {
        const idx = letter.toUpperCase().charCodeAt(0) - 65;
        return `${letter} — ${q.choices[idx]}`;
    })
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

    const quizDiv = document.getElementById("quiz");
    const resultDiv = document.getElementById("result");

    if (quizDiv) quizDiv.classList.add("hidden");

    if (resultDiv) {
        resultDiv.classList.remove("hidden");
        resultDiv.style.display = "block";

        resultDiv.innerHTML = `
            <h2>Exam Results</h2>
            <p><b>Score:</b> ${correct} / ${total} (${percent}%)</p>

            <button onclick="location.href='/history.html?attempt=${attemptId}'">
                📌 Review This Attempt
            </button>

            <button onclick="location.href='/history.html'">
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

    // Use quiz file path as key so each quiz tracks its own attempts
    const quizKey = (typeof QUIZ_FILE !== "undefined") ? QUIZ_FILE : "quiz.json";

    if (!store[quizKey]) {
        store[quizKey] = [];
    }

    store[quizKey].push({
        id: attemptId,
        date: new Date().toLocaleString(),
        score: correct,      // number of correct answers
        total: total,        // total questions
        percent: percent,    // percentage
        timeRemaining: timeRemaining,
        mode: "Exam",
        missed: missed       // array of {number, question, correct}
    });

    localStorage.setItem(HISTORY_KEY, JSON.stringify(store));
    console.log("History saved for quizKey:", quizKey, "Attempt:", attemptId);
}

