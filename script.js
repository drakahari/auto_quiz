/* =====================================================
   GLOBALS
===================================================== */
let quiz = [];
let index = 0;
let examMode = false;
let userAnswers = {};
let paused = false;

/* Timer state */
let examTimer = null;
let timeRemaining = 90 * 60;   // 90 minutes default

/* =====================================================
   LOAD QUIZ JSON
===================================================== */
async function loadQuiz() {
    try {
        console.log("Loading quiz file:", QUIZ_FILE);
        const res = await fetch(QUIZ_FILE);
        quiz = await res.json();

        console.log("Quiz loaded. Questions:", quiz.length);

        if (!quiz.length) {
            alert("No questions found in quiz file.");
        }
    } catch (err) {
        console.error("Failed to load quiz", err);
        alert("Could not load quiz file.");
    }
}

loadQuiz();

/* =====================================================
   START QUIZ
===================================================== */
function startQuiz(isExam) {
    examMode = isExam;
    index = 0;
    userAnswers = {};
    paused = false;
    timeRemaining = 90 * 60;

    document.getElementById("modeSelect")?.classList.add("hidden");
    document.getElementById("quiz")?.classList.remove("hidden");
    document.getElementById("result")?.classList.add("hidden");

    const timerBox = document.getElementById("timer");
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");

    if (examMode) {
        timerBox.classList.remove("hidden");
        startExamTimer();

        pauseBtn.classList.remove("hidden");
        resumeBtn.classList.add("hidden");
    } else {
        timerBox.classList.add("hidden");
        stopExamTimer();
    }

    renderQuestion();
    updateProgressBar();
}

/* =====================================================
   RENDER QUESTION
===================================================== */
function renderQuestion() {
    if (!quiz.length) return;

    const q = quiz[index];

    document.getElementById("qHeader").innerText =
        `Question ${index + 1} of ${quiz.length}`;

    document.getElementById("qText").innerText = q.question || "";

    const choicesDiv = document.getElementById("choices");
    choicesDiv.innerHTML = "";

    const correctLetters = q.correct.map(a => a.toUpperCase());
    const correctIndexes = correctLetters.map(l => l.charCodeAt(0) - 65);

    const selected = userAnswers[`q${index}`] || [];

    q.choices.forEach((choice, i) => {
        const btn = document.createElement("button");
        btn.className = "choice";
        btn.innerHTML = `<b>${String.fromCharCode(65 + i)}.</b> ${choice}`;

        // === STUDY MODE: Show correctness immediately ===
        if (!examMode && selected.includes(i)) {
            if (correctIndexes.includes(i)) {
                btn.classList.add("correct-choice");
            } else {
                btn.classList.add("wrong-choice");
            }
        }

        // === EXAM MODE: Just show selection ===
        if (examMode && selected.includes(i)) {
            btn.classList.add("selected");
        }

        btn.onclick = () => selectAnswer(index, i);
        choicesDiv.appendChild(btn);
    });

    updateProgressBar();
}

/* =====================================================
   SELECT ANSWER
===================================================== */
function selectAnswer(qIndex, choiceIndex) {
    const key = `q${qIndex}`;

    userAnswers[key] = [choiceIndex];

    renderQuestion();
}

/* =====================================================
   NAVIGATION
===================================================== */
function next() {
    if (index < quiz.length - 1) {
        index++;
        renderQuestion();
    }
}

function prev() {
    if (index > 0) {
        index--;
        renderQuestion();
    }
}

/* =====================================================
   PROGRESS BAR
===================================================== */
function updateProgressBar() {
    const filled = Object.keys(userAnswers).length;
    const pct = Math.round((filled / quiz.length) * 100);
    document.getElementById("progressBarInner").style.width = pct + "%";
}

/* =====================================================
   EXAM TIMER + PAUSE
===================================================== */
function startExamTimer() {
    const timeDisplay = document.getElementById("timeDisplay");

    if (examTimer) clearInterval(examTimer);

    examTimer = setInterval(() => {
        if (paused) return;

        timeRemaining--;

        let m = Math.floor(timeRemaining / 60);
        let s = timeRemaining % 60;

        timeDisplay.innerText = `${m}:${s.toString().padStart(2, "0")}`;

        if (timeRemaining <= 0) {
            clearInterval(examTimer);
            submitQuiz();
        }
    }, 1000);
}

function stopExamTimer() {
    if (examTimer) clearInterval(examTimer);
}

/* =====================================================
   PAUSE + RESUME
===================================================== */
function pauseExam() {
    console.log("PAUSE CLICKED");

    paused = true;

    document.getElementById("pauseOverlay").classList.add("show");
    document.body.classList.add("blurred");

    document.getElementById("pauseBtn").classList.add("hidden");
    document.getElementById("resumeBtn").classList.remove("hidden");

    console.log("Overlay class:",
        document.getElementById("pauseOverlay").className);
}

function resumeExam() {
    console.log("RESUME CLICKED");

    paused = false;

    document.getElementById("pauseOverlay").classList.remove("show");
    document.body.classList.remove("blurred");

    document.getElementById("pauseBtn").classList.remove("hidden");
    document.getElementById("resumeBtn").classList.add("hidden");
}

/* =====================================================
   SUBMIT EXAM
===================================================== */
function submitQuiz() {
    console.log("SUBMIT CLICKED!");

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
            missed.push({
                number: q.number || (i + 1),
                question: q.question,
                correct: q.correct
            });
        }
    });

    const percent = Math.round((correct / quiz.length) * 100);
    const attemptId = crypto.randomUUID();

    saveHistory(correct, percent, missed, attemptId);

    stopExamTimer();

    const resultEl = document.getElementById("result");
    resultEl.classList.remove("hidden");

    resultEl.innerHTML = `
        <h2>Results</h2>
        <p>Score: ${correct} / ${quiz.length} (${percent}%)</p>

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
}

/* =====================================================
   HISTORY STORAGE
===================================================== */
function saveHistory(score, percent, missed, attemptId) {
    let history = JSON.parse(localStorage.getItem("quizHistory") || "[]");

    history.push({
        id: attemptId,
        timestamp: new Date().toLocaleString(),
        score,
        percent,
        total: quiz.length,
        missed
    });

    localStorage.setItem("quizHistory", JSON.stringify(history));
}
