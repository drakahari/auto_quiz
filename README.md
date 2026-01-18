This is version 1.1
Created on 1/9/26 by Mike Buchanan

# DLMS – Digital Learning & Management System

DLMS is a self-hosted quiz and learning application designed for study, practice,
and exam preparation. It supports both **Study Mode** and **Exam Mode**, detailed
attempt history, confidence analysis, and Anki export for long-term retention.

## Why DLMS Exists

DLMS was created to address a gap between simple quiz tools and full-scale learning
management systems. Many existing solutions are either too limited for serious
study or too complex, restrictive, or heavyweight for individual learners,
educators, and IT professionals.

DLMS is designed to be local, transparent, and learner-focused. It gives users full
control over their content, data, and study workflow without requiring cloud
accounts, subscriptions, or external services. By running entirely on the user’s
system as a local web application, DLMS prioritizes privacy, reliability, and
portability.

For users who prefer deeper system integration, DLMS can also be enabled as a
systemd service (this is what I do).

The project emphasizes learning effectiveness, not just assessment. Features like
Study Mode, confidence analysis, attempt history, and Anki export are intended to
help users identify weak areas, reinforce understanding, and retain knowledge over
time—especially in certification, technical training, and self-directed study
scenarios.

DLMS exists because effective learning tools should be:

* Powerful without being bloated
* Flexible without being fragile
* Private by default
* Open for inspection, improvement, and reuse

DLMS runs as a **local web application**.

---

## 🚀 How to Use DLMS (Important)

After starting DLMS, **open a web browser** and go to:

👉 **[http://127.0.0.1:9001/](http://127.0.0.1:9001/)**

This is the main interface for the application.

DLMS does **not** open a browser automatically.

---

## ✨ Key Features

* Study Mode and Exam Mode
* Upload or paste quiz questions
* Advanced parsing tools using regular expressions (regex)
* Attempt history and performance tracking
* Confidence analysis (optional)
* Export missed questions to **Anki**
* Custom quiz logos and portal appearance

---

## 🧠 Study Mode & Learning Tools

Study Mode is designed to help users learn and reinforce concepts rather than
simulate a timed exam. Users can review questions, analyze confidence levels, and
focus on missed material.

(See screenshots below. No logos or quiz questions/answers are provided.)

### Study Mode Examples

![Study Mode Example 1](docs/screenshots/SS1.png)
![Study Mode Example 2](docs/screenshots/SS2.png)

### Anki Export Examples

![Anki Export Example 1](docs/screenshots/anki1.png)
![Anki Export Example 2](docs/screenshots/anki2.png)

---

## 🧩 Anki Integration

DLMS supports exporting missed questions to Anki, a proven spaced-repetition
learning system. This allows users to turn weak areas into targeted study decks
for long-term retention.

---

## 🖥️ Running DLMS

### From a prebuilt binary (recommended)

1. Download the appropriate binary for your operating system from **Releases**
2. Run the DLMS executable
3. Open a browser and go to **[http://127.0.0.1:9001/](http://127.0.0.1:9001/)**

### From source (advanced users)

```bash
python app.py
```

---

## 📂 Data & Configuration

On first run, DLMS creates its data directory in your user profile and initializes
its database and configuration files automatically.

No external database or web server is required.

---

## 📘 Question & Answer Formatting (Important)

DLMS relies on a clear and consistent question format in order to correctly parse
quiz content. Each question **must include an explicit answer line** so the system
knows which option or options are correct.

### ✅ Required Answer Line

Every question must end with **one** of the following:

* `Suggested Answer: X`
* `Correct Answer: X`

Where `X` is:

* A single letter (e.g., `A`)
* Multiple letters for multi-answer questions (e.g., `AC`)

Both formats are treated identically by DLMS.

---

### 🧪 Example: Single-Answer Question

```
1. Which component is responsible for providing electrical power to a computer system?

A. Motherboard
B. Power supply
C. CPU
D. Hard drive

Suggested Answer: B
```

---

### 🧪 Example: Multi-Answer Question

```
2. Which of the following are common operating system functions?
(Choose two.)

A. Memory management
B. Power distribution
C. Process scheduling
D. Monitor calibration
E. File system management

Correct Answer: AC
```

---

### 🧪 Example: Alternate Accepted Format

```
3. What does DNS primarily resolve?

A. MAC addresses to IP addresses
B. IP addresses to hostnames
C. Hostnames to IP addresses
D. Ports to services

Correct Answer: C
```

`Suggested Answer:` and `Correct Answer:` are interchangeable.

---

### ⚠️ Formatting Notes & Best Practices

* Answer letters must match the choices exactly
* Do **not** include punctuation or words in the answer line

  * ❌ `Correct Answer: A, C`
  * ❌ `Suggested Answer: A and C`
  * ✅ `Correct Answer: AC`
* Question numbers are optional but recommended
* Blank lines between questions are allowed
* Extra whitespace is ignored safely

---

### 🧠 Tip for Pasted Questions

If you are pasting questions from PDFs, documents, or study guides, DLMS includes
regex-based parsing tools to help clean and normalize formatting before upload.
Use these tools carefully to ensure answer lines remain intact.

---

## 🧹 Removing DLMS & Cleaning Up Files

DLMS does not install system-wide dependencies or background services by default.
Removing the application is straightforward.

### 🪟 Windows Cleanup

1. Close DLMS and stop the application
2. Delete the DLMS executable
3. Remove the application data directory:

```
C:\Users\<YourUsername>\AppData\Roaming\DLMS
```

(Optional) If you ran development or test builds, you may also remove:

```
C:\Users\<YourUsername>\AppData\Local\Temp\_MEI*
```

These temporary folders are created by PyInstaller and are safe to delete.

---

### 🐧 Linux Cleanup

1. Stop DLMS if it is running
2. Remove the DLMS binary or source directory
3. Remove the application data directory:

```
~/.local/share/DLMS
```

(Optional) If you enabled DLMS as a systemd service, disable and remove it:

```bash
sudo systemctl stop DLMS
sudo systemctl disable DLMS
sudo rm /etc/systemd/system/DLMS.service
sudo systemctl daemon-reload
```

No additional cleanup is required. DLMS leaves no background services or hidden
files once removed.
