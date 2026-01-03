/* =====================================================
   GLOBALS
===================================================== */
let quiz = [];
let index = 0;
let examMode = false;
let userAnswers = {};
let paused = false;

let examTimer = null;
let timeRemaining = 90 * 60; 

/* =====================================================
   LOAD QUIZ
===================================================== */
async function loadQuiz() {
    console.log("Loading quiz file:", QUIZ_FILE);

    const res = await fetch(QUIZ_FILE);
    quiz = await res.json();

    console.log("Quiz loaded. Questions:", quiz.length);
}

loadQuiz();

/* =====================================================
   RENDER QUESTION
===================================================== */
function renderQuestion() {
    if (!quiz.length) return;

    const q = quiz[index];

    document.getElementById("qHeader").innerText =
        "Question " + (index + 1) + " of " + quiz.length;

    document.getElementById("qText").innerText = q.question;

    let html = "";
    q.choices.forEach((c, i) => {
        const key = `q${index}`;
        const selected = userAnswers[key]?.includes(i) ? "selected" : "";

        html += `
        <div class="choice ${selected}" onclick="selectChoice(${i})">
            ${String.fromCharCode(65 + i)}) ${c}
        </div>`;
    });

    document.getElementById("choices").innerHTML = html;
    updateProgressBar();
}

/* =====================================================
   ANSWER SELECT
===================================================== */
function selectChoice(i) {
    const key = `q${index}`;
    userAnswers[key] = [i];
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
    const percent = ((index + 1) / quiz.length) * 100;
    document.getElementById("progressBarInner").style.width = percent + "%";
}

/* =====================================================
   START QUIZ
===================================================== */
function startQuiz(isExam) {
    examMode = isExam;
    index = 0;
    userAnswers = {};
    paused = false;

    document.getElementById("modeSelect").classList.add("hidden");
    document.getElementById("quiz").classList.remove("hidden");
    document.getElementById("result").classList.add("hidden");

    const timer = document.getElementById("timer");
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");

    if (examMode) {
        timeRemaining = 90 * 60;
        timer.classList.remove("hidden");
        pauseBtn.classList.remove("hidden");
        resumeBtn.classList.add("hidden");
        startExamTimer();
    } else {
        timer.classList.add("hidden");
    }

    renderQuestion();
}

/* =====================================================
      EXAM TIMER
===================================================== */
function startExamTimer() {
    const display = document.getElementById("timeDisplay");

    if (examTimer) clearInterval(examTimer);

    examTimer = setInterval(() => {
        if (paused) return;

        timeRemaining--;

        const m = Math.floor(timeRemaining / 60);
        const s = timeRemaining % 60;

        display.innerText = `${m}:${s.toString().padStart(2,"0")}`;

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

    document.body.classList.add("blurred");
    document.getElementById("pauseOverlay").classList.add("show");

    document.getElementById("pauseBtn").classList.add("hidden");
    document.getElementById("resumeBtn").classList.remove("hidden");
}

function resumeExam() {
    console.log("RESUME CLICKED");
    paused = false;

    document.body.classList.remove("blurred");
    document.getElementById("pauseOverlay").classList.remove("show");

    document.getElementById("pauseBtn").classList.remove("hidden");
    document.getElementById("resumeBtn").classList.add("hidden");
}

/* =====================================================
   SUBMIT QUIZ
===================================================== */
function submitQuiz() {
    console.log("SUBMIT CLICKED!");

    if (!quiz || !quiz.length) {
        alert("Quiz not loaded");
        return;
    }

    let correct = 0;
    let missed = [];

    quiz.forEach((q, i) => {
        const key = `q${i}`;
        const answer = userAnswers[key];

        const correctLetters = q.correct.map(a => a.toUpperCase());
        const correctIndexes = correctLetters.map(l => l.charCodeAt(0) - 65);

        if (JSON.stringify(answer) === JSON.stringify(correctIndexes)) {
            correct++;
        } else {
            missed.push({
                number: q.number,
                question: q.question,
                correct: q.correct
            });
        }
    });

    stopExamTimer();

    const score = Math.round((correct / quiz.length) * 100);

    document.getElementById("quiz").classList.add("hidden");

    document.getElementById("result").innerHTML = `
        <h2>Results</h2>
        <p><b>Score:</b> ${correct} / ${quiz.length} (${score}%)</p>
    `;

    document.getElementById("result").classList.remove("hidden");

    saveHistory(score);
}

/* =====================================================
   SAVE HISTORY
===================================================== */
function saveHistory(score) {
    let history = JSON.parse(localStorage.getItem("history") || "[]");

    history.push({
        date: new Date().toLocaleString(),
        score: score
    });

    localStorage.setItem("history", JSON.stringify(history));
}
