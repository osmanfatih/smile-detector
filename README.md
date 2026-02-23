# 😄 Smile Detector

A fully offline web app that detects smiles using your webcam and rewards participants who flash a big grin.

## How It Works

1. Open the app in your browser → it accesses your webcam
2. **MediaPipe Face Mesh** analyses your face 5× per second
3. Three tiers:
   - 😐 **No smile** → "Come on, show us that smile!"
   - 🙂 **Small smile** → "Almost there — give us a bigger smile!"
   - 😁 **Full smile** (held for 1 second) → Confetti 🎉 + email form slides in
4. User enters name + email → stored in local SQLite DB
5. Admin can view all submissions at `/emails`

---

## Setup

### 1. Install dependencies

```bash
cd smile-detector
pip install -r requirements.txt
```

> First run downloads the MediaPipe model (~4 MB, cached after that).  
> Everything else works **fully offline**.

### 2. Run the app

```bash
python main.py
```

or with uvicorn directly:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Open the app

Navigate to: **http://localhost:8000**

Allow camera permissions when prompted.

---

## Admin

View collected name + email submissions:

```
GET http://localhost:8000/emails
```

The SQLite database is stored at `smile_submissions.db` in the project root.

---

## Smile Detection Tuning

Smile score thresholds are in `detector.py`:

```python
SMALL_SMILE_THRESHOLD = 0.30   # below this = no smile
FULL_SMILE_THRESHOLD  = 0.55   # above this = full smile (triggers form)
```

The score is derived from MediaPipe Face Mesh landmark geometry:
- How much the mouth corners (landmarks 61 & 291) are raised relative to the lip center (13, 14)
- Normalized by lower face height (nose tip to chin)

If detection feels too sensitive or not sensitive enough, adjust these thresholds.

---

## Tech Stack

| Component | Tech |
|-----------|------|
| Backend   | Python + FastAPI + Uvicorn |
| CV Model  | MediaPipe Face Mesh |
| Transport | WebSocket (base64 JPEG frames at 5fps) |
| Storage   | SQLite via SQLAlchemy + aiosqlite |
| Frontend  | Vanilla HTML/CSS/JS (no CDN, works offline) |
