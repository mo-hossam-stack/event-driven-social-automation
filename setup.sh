#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DJANGO_ADMIN_USER="${DJANGO_ADMIN_USER:-admin}"
DJANGO_ADMIN_PASSWORD="${DJANGO_ADMIN_PASSWORD:-admin123}"
DJANGO_ADMIN_EMAIL="${DJANGO_ADMIN_EMAIL:-admin@example.com}"

echo "=== Event-Driven Social Automation — Setup ==="

# ── 1. Check prerequisites ──────────────────────────────────────
echo "→ Checking prerequisites..."

command -v uv >/dev/null || {
    echo "✗ uv is required. Install: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

echo "  uv: $(uv --version)"

if command -v docker >/dev/null; then
    echo "  docker: $(docker --version)"
else
    echo "  ⚠ Docker not found — Inngest dev server won't work"
fi

# ── 2. Verify project structure ──────────────────────────────────
if [ ! -d backend ]; then
    echo "✗ backend/ directory not found — are you in the project root?"
    exit 1
fi

if [ ! -f pyproject.toml ]; then
    echo "✗ pyproject.toml not found — are you in the project root?"
    exit 1
fi

# ── 3. Install dependencies ──────────────────────────────────────
echo "→ Installing dependencies..."

uv sync --dev

echo "✓ Dependencies installed"

# ── 4. Ensure .env exists ────────────────────────────────────────
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        echo "→ Copying backend/.env.example → backend/.env"
        cp backend/.env.example backend/.env
    else
        echo "✗ backend/.env.example missing — cannot create .env"
        exit 1
    fi
else
    echo "→ backend/.env already exists, skipping copy"
fi

# ── 5. Run migrations (validates Django config implicitly) ───────
echo "→ Running migrations..."
uv run python backend/manage.py migrate --noinput
echo "✓ Migrations complete"

# ── 6. Create superuser (idempotent) ─────────────────────────────
echo "→ Creating superuser..."
export DJANGO_ADMIN_USER DJANGO_ADMIN_PASSWORD DJANGO_ADMIN_EMAIL

uv run python backend/manage.py shell -c "
import os
from django.contrib.auth.models import User
username = os.environ['DJANGO_ADMIN_USER']
email = os.environ['DJANGO_ADMIN_EMAIL']
password = os.environ['DJANGO_ADMIN_PASSWORD']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'  Superuser created: {username}')
else:
    print(f'  Superuser \"{username}\" already exists, skipping')
"

# ── 7. Django system check ───────────────────────────────────────
echo "→ Running Django system checks..."
uv run python backend/manage.py check
echo "✓ Django configuration valid"

echo ""
echo "=== Setup complete ==="
echo ""
echo "  ✓ Dependencies installed"
echo "  ✓ Database migrated"
echo "  ✓ Admin user available (${DJANGO_ADMIN_USER})"
echo "  ✓ Django configuration valid"
echo ""
echo "  Next steps:"
echo "    rav server            # Django dev server → http://localhost:8000"
echo "    rav scheduler_server  # Inngest dev server → http://localhost:8288"
echo "    rav setup             # Re-run this script"
