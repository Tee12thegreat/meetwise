# MeetWise — Smart Meeting Scheduler & Minutes Platform

A professional Django prototype for scheduling meetings, running video conferences,
and capturing structured meeting minutes.

---

## Features

- **Dashboard** — at-a-glance view of upcoming and past meetings, stats
- **Meeting Scheduler** — create meetings with title, agenda, attendees, time & duration
- **Meeting Detail** — full view with status, agenda, attendees, and minutes
- **Video Conferencing** — custom full-screen conference room powered by Jitsi Meet
  - Live timer, agenda checklist, live note-taking panel, participants list
  - Start/end meeting controls for the organiser
- **Meeting Minutes** — structured form for notes, decisions, and action items
- **Status Flow** — Scheduled → In Progress → Completed / Cancelled
- **Auth** — Django's built-in login/logout with a custom branded login page

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- pip

### 2. Install & Run

```bash
# Clone / unzip the project, then:
cd meetwise

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo users and meetings
python manage.py seed_demo

# Start the server
python manage.py runserver
```

Then open **http://127.0.0.1:8000**

Or simply run `./setup.sh` which does all of the above in one step.

---

## Demo Accounts

| Username | Password  | Role       |
|----------|-----------|------------|
| admin    | admin123  | Organiser (superuser) |
| sarah    | sarah123  | Attendee   |
| james    | james123  | Attendee   |

Django Admin: **http://127.0.0.1:8000/admin** (login with admin / admin123)

---

## Project Structure

```
meetwise/
├── meetwise/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── meetings/               # Main app
│   ├── models.py           # Meeting, MeetingMinutes
│   ├── views.py            # All views
│   ├── forms.py            # MeetingForm, MinutesForm
│   ├── urls.py             # URL routing
│   ├── admin.py            # Django admin registration
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo.py
│   └── templates/
│       └── meetings/
│           ├── base.html         # App shell with sidebar
│           ├── login.html        # Branded login page
│           ├── dashboard.html    # Home dashboard
│           ├── meeting_list.html # All meetings with filters
│           ├── schedule.html     # Schedule new meeting
│           ├── detail.html       # Meeting detail
│           ├── conference.html   # Full-screen video conference
│           └── minutes.html      # Minutes editor
├── requirements.txt
├── setup.sh
└── manage.py
```

---

## Video Conferencing

The conference room uses the **Jitsi Meet** public API (meet.jit.si) — no account
or API key required. Each meeting gets a unique room code automatically generated
from its UUID. The conference page features:

- Embedded Jitsi video call (camera, mic, screen share, chat, recording)
- Live meeting timer
- Side panel: live notes, agenda checklist, participants list
- Notes are saved to localStorage and can be copied into the minutes form
- Start/End controls for the organiser

> **Note:** In production, you'd self-host a Jitsi server or use a paid service
> like Daily.co or Twilio for privacy and reliability.

---

## Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Framework  | Django 4.2                    |
| Database   | SQLite (dev) / PostgreSQL prod|
| Auth       | Django built-in auth          |
| Video      | Jitsi Meet External API       |
| Fonts      | Cormorant Garamond + DM Sans  |
| Styling    | Vanilla CSS (design system)   |
| Static     | WhiteNoise (optional)         |

---

## Production Checklist

- [ ] Set `DEBUG = False` and configure `SECRET_KEY` via env variable
- [ ] Switch to PostgreSQL
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Enable WhiteNoise or serve static files via nginx
- [ ] Add email backend for meeting invitations
- [ ] Self-host Jitsi or use a paid WebRTC provider
- [ ] Add HTTPS (Let's Encrypt)
