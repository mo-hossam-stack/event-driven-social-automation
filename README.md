# Event-Driven Social Automation

<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0" />
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/Inngest-Event--Driven-32A7C2?style=for-the-badge" alt="Inngest" />
  <img src="https://img.shields.io/badge/django--allauth-LinkedIn--OAuth-CC6699?style=for-the-badge" alt="django-allauth LinkedIn OAuth" />
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Docker-Scheduler-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/uv-Package--Manager-2F3134?style=for-the-badge&logo=uv&logoColor=white" alt="uv" />
  <img src="https://img.shields.io/badge/rav-Task--Runner-404040?style=for-the-badge" alt="rav" />
</p>

A Django-based LinkedIn post scheduler using **Inngest** for event-driven scheduling. Create posts (via admin or web UI) and the system auto-publishes them to LinkedIn at a scheduled time.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager)
- Docker (optional, required for Inngest dev server)

## Quick Start

```bash
git clone https://github.com/mo-hossam-stack/event-driven-social-automation
cd event-driven-social-automation
./setup.sh
```

The script will:
1. Verify prerequisites
2. Install dependencies (`uv sync --dev`)
3. Copy `.env.example` → `.env` if missing
4. Run database migrations
5. Create a superuser (`admin` / `admin123`)
6. Run Django system checks

### Override admin credentials

```bash
DJANGO_ADMIN_USER=myuser DJANGO_ADMIN_PASSWORD=mypass ./setup.sh
```

## Running

Start the Django dev server and Inngest in separate terminals:

```bash
# Terminal 1 — Django
rav server
# → http://localhost:8000

# Terminal 2 — Inngest (requires Docker)
rav scheduler_server
# → http://localhost:8288
```

## LinkedIn OAuth Setup

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app with **"Sign In with LinkedIn using OpenID Connect"** and **"Share on LinkedIn"** products
3. Set redirect URI to: `http://localhost:8000/accounts/linkedin/login/callback/`
4. Copy your Client ID and Secret into `backend/.env`:
   ```
   LINKEDIN_CLIENT_ID=your-client-id
   LINKEDIN_CLIENT_SECRET=your-client-secret
   ```
5. Restart the server and visit `http://localhost:8000/accounts/linkedin/login/`


## Re-running Setup

```bash
rav setup
# or
./setup.sh
```

Idempotent — safe to run multiple times.
