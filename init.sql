PRAGMA foreign_keys = ON;

/* =====================================================
   QUIZZES (One record per quiz set)
===================================================== */
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* =====================================================
   QUESTIONS (Each quiz question)
===================================================== */
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    number INTEGER NOT NULL,
    text TEXT NOT NULL,

    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        ON DELETE CASCADE
);

/* =====================================================
   CHOICES (Answer options A–Z)
===================================================== */
CREATE TABLE IF NOT EXISTS choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    label TEXT NOT NULL,          -- "A", "B", "C", etc.
    text TEXT NOT NULL,
    is_correct INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (question_id) REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   ATTEMPTS (When a user completes an exam)
===================================================== */
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,          -- Use your existing UUID
    quiz_id INTEGER NOT NULL,

    user_name TEXT,               -- Optional / future
    started_at DATETIME,
    completed_at DATETIME,

    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    percent INTEGER NOT NULL,
    time_remaining INTEGER,
    mode TEXT NOT NULL,           -- "Exam" or "Study"

    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        ON DELETE CASCADE
);

/* =====================================================
   ATTEMPT ANSWERS (What user selected)
===================================================== */
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,

    selected_labels TEXT,         -- "A" or "A,C"
    was_correct INTEGER NOT NULL,

    FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        ON DELETE CASCADE,

    FOREIGN KEY (question_id) REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   OPTIONAL: MISSED QUESTIONS TABLE
   (Convenience table — everything here could be derived,
    but storing it makes analytics easier)
===================================================== */
CREATE TABLE IF NOT EXISTS missed_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    correct_labels TEXT NOT NULL, -- "B", "A,D", etc.

    FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        ON DELETE CASCADE,

    FOREIGN KEY (question_id) REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   INDEXES (Performance Boost)
===================================================== */
CREATE INDEX IF NOT EXISTS idx_questions_quiz
    ON questions (quiz_id);

CREATE INDEX IF NOT EXISTS idx_choices_question
    ON choices (question_id);

CREATE INDEX IF NOT EXISTS idx_attempts_quiz
    ON attempts (quiz_id);

CREATE INDEX IF NOT EXISTS idx_answers_attempt
    ON attempt_answers (attempt_id);

CREATE INDEX IF NOT EXISTS idx_answers_question
    ON attempt_answers (question_id);

/* =====================================================
   META INFO (Future migrations / versioning)
===================================================== */
CREATE TABLE IF NOT EXISTS schema_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_meta (id, version)
VALUES (1, 1);
