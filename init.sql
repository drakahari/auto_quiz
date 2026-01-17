PRAGMA foreign_keys = ON;

/* =====================================================
   QUIZZES (One record per quiz set)
===================================================== */
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Human-readable name (NOT unique)
    title TEXT NOT NULL,

    -- Canonical identity (filename or source identifier)
    source_file TEXT NOT NULL UNIQUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* =====================================================
   QUESTIONS (Each quiz question)
===================================================== */
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    quiz_id INTEGER NOT NULL,

    -- Original question number from the source quiz
    question_number INTEGER NOT NULL,

    question_text TEXT NOT NULL,
    correct_letters TEXT,
    correct_text TEXT,

    -- Prevent accidental duplicate imports of the same question
    UNIQUE (quiz_id, question_number, question_text),

    FOREIGN KEY (quiz_id)
        REFERENCES quizzes(id)
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

    FOREIGN KEY (question_id)
        REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   ATTEMPTS (One quiz run — Study or Exam)
===================================================== */
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,          -- UUID / timestamp-based ID
    quiz_id INTEGER NOT NULL,

    user_name TEXT,
    started_at DATETIME,
    completed_at DATETIME,

    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    percent INTEGER NOT NULL,
    time_remaining INTEGER,
    mode TEXT NOT NULL,           -- "Exam" or "Study"

    FOREIGN KEY (quiz_id)
        REFERENCES quizzes(id)
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

    FOREIGN KEY (attempt_id)
        REFERENCES attempts(id)
        ON DELETE CASCADE,

    FOREIGN KEY (question_id)
        REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   MISSED QUESTIONS (Analytics convenience table)
===================================================== */
CREATE TABLE IF NOT EXISTS missed_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    attempt_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    correct_letters TEXT NOT NULL,

    FOREIGN KEY (attempt_id)
        REFERENCES attempts(id)
        ON DELETE CASCADE,

    FOREIGN KEY (question_id)
        REFERENCES questions(id)
        ON DELETE CASCADE
);

/* =====================================================
   INDEXES (Performance)
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
   SCHEMA META (Version tracking)
===================================================== */
CREATE TABLE IF NOT EXISTS schema_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_meta (id, version)
VALUES (1, 1);
