# Event-Driven Social Automation

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
