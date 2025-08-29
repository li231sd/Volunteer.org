# Volunteer.org

#### Video Demo (Old Version): https://youtu.be/yiV0YpSmPW0

# Volunteer.org - Refactored Flask Application

This document explains the new modular structure of the Volunteer.org Flask application.

## Directory Structure

```
Volunteer.org/
│
├── app.py                # Entry point, creates and runs the app
├── config.py             # Configuration settings
├── db.py                 # Database connection and helpers
├── email_utils.py        # Email sending functions
├── routes/
│   ├── __init__.py       # Registers all blueprints
│   ├── auth.py           # Login, logout, register routes
│   ├── events.py         # Event-related routes (register, RSVP, delete, etc.)
│   ├── staff.py          # Staff login and review routes
│   └── user.py           # User-specific routes (history, my events, etc.)
├── static/
├── templates/
└── volunteer.db
```
