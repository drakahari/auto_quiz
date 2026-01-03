/* =====================================================
      GLOBAL STATE
===================================================== */
let quiz = [];
let index = 0;
let userAnswers = {};
let examMode = false;
let paused = false;
let savedTime = 0;


const HISTORY_KEY = "serverplus_history_v2";

/* =====================================================
      LOAD QUIZ JSON
===================================================== */
async function loadQuiz() {
    try {
        const file = (typeof QUIZ_FILE !== "undefined") ? QUIZ_FILE : "quiz.json";
        console.log("Loading quiz file:", file);

        const res = await fetch(file, { cache: "no-store" });
        quiz = await res.json();

        if (!Array.isArray(quiz) || !quiz.length) {
            alert("Quiz JSON invalid or empty");
            return;
        }

        console.log("Loaded quiz with", quiz.length, "questions");
    } catch (err) {
        console.error(err);
        alert("Could not load quiz JSON");
    }
}

/* =====================================================
      START QUIZ
===================================================== */
function startQuiz(isExam) {
    examMode = isExam;
    index = 0;
    userAnswers = {};

    document.getElementById("modeSelect")?.classList.add("hidden");
    document.getElementById("quiz")?.classList.remove("hidden");
    document.getElementById("result")?.classList.add("hidden");

    const submitBtn = document.querySelector("button[onclick='submitQuiz()']");
    if (submitBtn) submitBtn.style.display = examMode ? "inline-block" : "none";

    if (examMode) startExamTimer();
    else stopExamTimer();

    renderQuestion();
    updateProgressBar();
}

/* =====================================================
      RENDER QUESTION
===================================================== */
function renderQuestion() {
    if (!quiz.length) return;

    const q = quiz[index];
    const key = `q${index}`;

    const headerEl = document.getElementById("qHeader");
    const textEl = document.getElementById("qText");
    const choicesEl = document.getElementById("choices");

    if (headerEl) headerEl.innerText = `Question ${index + 1} of ${quiz.length}`;
    if (textEl) textEl.innerText = q.question || "";

    const selected = userAnswers[key] || [];

    const correctLetters = q.correct.map(c => c.toUpperCase());
    const correctIndexes = correctLetters.map(l => l.charCodeAt(0) - 65);

    let html = "";

    q.choices.forEach((choice, i) => {
        const letter = String.fromCharCode(65 + i);
        let extraClass = "";

        if (!examMode) {
            // Study Mode feedback
            if (selected.includes(i)) {
                extraClass = correctIndexes.includes(i) ? "correct-choice" : "wrong-choice";
            } else if (selected.length && correctIndexes.includes(i)) {
                extraClass = "correct-choice";
            }
        } else {
            if (selected.includes(i)) extraClass = "selected";
        }

        html += `
        <button class="choice ${extraClass}"
            onclick="selectAnswer(${index}, ${i})">
            <b>${letter}.</b> ${choice}
        </button>`;
    });

    if (choicesEl) choicesEl.innerHTML = html;
    updateProgressBar();
}

/* =====================================================
      SELECT ANSWER
===================================================== */
function selectAnswer(qIndex, cIndex) {
    const key = `q${qIndex}`;

    userAnswers[key] = [cIndex];

    renderQuestion();
}

/* =====================================================
      NAVIGATION
===================================================== */
function next() {
    if (index < quiz.length - 1) {
        index++;

        if (!examMode) delete userAnswers[`q${index}`];

        renderQuestion();
    }
}

function prev() {
    if (index > 0) {
        index--;

        if (!examMode) delete userAnswers[`q${index}`];

        renderQuestion();
    }
}

/* =====================================================
      PROGRESS
===================================================== */
function updateProgressBar() {
    const bar = document.getElementById("progressBarInner");
    if (!bar) return;

    const percent = ((index + 1) / quiz.length) * 100;
    bar.style.width = percent + "%";
}

/* =====================================================
      SUBMIT (Exam Mode)
===================================================== */
function submitQuiz() {
    console.log("SubmitQuiz running…");

    try {
        let correct = 0;
        let missed = [];

        quiz.forEach((q, i) => {
            const key = `q${i}`;
            const ans = userAnswers[key];

            const correctLetters = q.correct.map(a => a.toUpperCase());
            const correctIndexes = correctLetters.map(l => l.charCodeAt(0) - 65);

            if (JSON.stringify(ans) === JSON.stringify(correctIndexes)) {
                correct++;
            } else {
                missed.push(q.number || (i + 1));
            }
        });

        const percent = Math.round((correct / quiz.length) * 100);
        console.log("Score computed:", correct, percent);

        // ⭐ Safe attemptId with fallback
        let attemptId;
        try {
            attemptId = crypto.randomUUID();
        } catch {
            attemptId = "attempt_" + Date.now() + "_" + Math.random().toString(36).slice(2);
            console.warn("crypto.randomUUID not supported – using fallback:", attemptId);
        }

        saveHistory(correct, percent, missed, attemptId);
        stopExamTimer();

        const resultEl = document.getElementById("result");
        if (!resultEl) {
            alert("ERROR: <div id='result'> is missing from quiz HTML");
            console.error("Result element missing in page");
            return;
        }

        resultEl.classList.remove("hidden");
        resultEl.innerHTML = `
            <h2>Results</h2>
            <p>Score: ${correct} / ${quiz.length} (${percent}%)</p>
            <p>Missed: ${missed.join(", ") || "None 🎉"}</p>

            <br>

            <button onclick="location.href='/history.html?attempt=${attemptId}'">
                📌 Review JUST This Attempt
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

        console.log("Results displayed successfully");

    } catch (e) {
        console.error("Submit crashed!", e);
        alert("Submit crashed! Check console for details");
    }
}


/* =====================================================
      HISTORY SAVE — WITH DETAILS + ATTEMPT ID
===================================================== */
function saveHistory(score, percent, missed, attemptId) {
    const store = JSON.parse(localStorage.getItem(HISTORY_KEY) || "{}");
    const key = QUIZ_FILE;

    if (!store[key]) store[key] = [];

    let missedDetails = missed.map(mNum => {
        let q = quiz.find(q => (q.number || 0) === mNum);
        if (!q) return null;

        const correctLetter = q.correct[0];
        const idx = correctLetter.charCodeAt(0) - 65;
        const correctText = q.choices[idx];

        return {
            number: mNum,
            question: q.question,
            correctLetter,
            correctText
        };
    }).filter(Boolean);

    store[key].push({
        attemptId,
        date: new Date().toLocaleString(),
        mode: examMode ? "Exam" : "Study",
        score,
        total: quiz.length,
        percent,
        missed,
        missedDetails,
        timeRemaining
    });

    localStorage.setItem(HISTORY_KEY, JSON.stringify(store));
}

/* =====================================================
      EXAM TIMER + PAUSE
===================================================== */

let examTimer = null;
/*let paused = false; */
let timeRemaining = 90 * 60;   // 90 minutes default

function startExamTimer() {
    const timeDisplay = document.getElementById("timeDisplay");

    // Prevent multiple timers
    if (examTimer) clearInterval(examTimer);

    examTimer = setInterval(() => {
        if (paused) return;

        timeRemaining--;

        const m = Math.floor(timeRemaining / 60);
        const s = timeRemaining % 60;

        timeDisplay.innerText = `${m}:${s.toString().padStart(2, "0")}`;

        if (timeRemaining <= 0) {
            clearInterval(examTimer);
            submitQuiz();
        }

    }, 1000);
}

function togglePause() {
    const overlay = document.getElementById("pauseOverlay");
    const btn = document.getElementById("pauseBtn");

    paused = !paused;

    if (paused) {
        overlay.classList.remove("hidden");
        overlay.style.display = "flex";
        btn.innerText = "▶ Resume Exam";
    } else {
        overlay.classList.add("hidden");
        overlay.style.display = "none";
        btn.innerText = "⏸ Pause Exam";
    }
}

function stopExamTimer() {
    if (examTimer) clearInterval(examTimer);
}

/* =====================================================
      START
===================================================== */
window.onload = loadQuiz;
