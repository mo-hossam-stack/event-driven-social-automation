# ADR-002: SQLite Database Choice

**Status**: Accepted (Development Only)

**Date**: 2024 (inferred from project creation)

**Decision Makers**: Mohamed Hossam

## Context

The project needs a database to store:
- User accounts
- OAuth tokens and social account linkages (django-allauth)
- Scheduled posts with metadata
- Django sessions

**Requirements**:
- Easy local setup for tutorial
- No external dependencies for students
- Support Django ORM
- Handle development workload (< 100 concurrent users)

**Alternatives Considered**:
1. **SQLite** (chosen for development)
2. **PostgreSQL** (production)
3. **MySQL**
4. **MongoDB** 

## Decision

Use **SQLite** for development and tutorials, with explicit guidance to migrate to **PostgreSQL or MySQL** for production use.

## Rationale

### Chosen Approach: SQLite (Development)

**Advantages**:
- ✅ Zero configuration (file-based)
- ✅ No separate database server required
- ✅ Built into Python standard library
- ✅ Perfect for tutorials and local development
- ✅ Database file portable and easy to backup
- ✅ No authentication or network configuration
- ✅ Works instantly on Windows, Mac, Linux

**Disadvantages**:
- ❌ No concurrent write support (global write lock)
- ❌ Not suitable for production
- ❌ Limited scalability
- ❌ No built-in replication
- ❌ File corruption risk under load
- ❌ No user/role management

### Alternative 1: PostgreSQL

**Why Not Chosen for Development**:
- Requires installation and configuration
- Database server must be running
- Complicates tutorial setup

**When to Use**:
- Production deployments
- Multi-user scenarios
- Need for concurrent writes
- Require advanced features (JSON fields, full-text search)

### Alternative 2: MySQL

**Why Not Chosen**:
- Same complexity as PostgreSQL for setup
- PostgreSQL preferred in Django community
- No significant advantages over PostgreSQL for this use case

### Alternative 3: MongoDB

**Why Not Chosen**:
- Django ORM designed for relational databases
- Requires additional libraries (djongo, pymongo)
- Relational model better fits this use case
- Adds unnecessary complexity

## Consequences

### Positive

- Students can start coding immediately (no database setup)
- Migrations work out of the box
- Database file easy to inspect (DB Browser for SQLite)
- Simple backup/restore (copy file)
- Low barrier to entry for tutorial

### Negative

- Concurrent post creation may experience write lock contention
- Production deployment requires database migration
- Students might deploy to production with SQLite (dangerous)
- Schema differences between SQLite and production database

### Mitigation Strategies

1. **Documentation**: Clear warnings that SQLite is development-only
2. **Production Guide**: Provide PostgreSQL migration instructions
3. **Settings Organization**: Separate development and production settings
4. **Database URL**: Use environment variable for production database

**Recommended Production Configuration**:
```python
# Production settings.py
import os
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://user:pass@localhost:5432/dbname'
    )
}
```

## Production Database Recommendation

### PostgreSQL 12+ (Recommended)

**Advantages**:
- Excellent Django support
- ACID compliant
- Strong community
- JSON field support
- Full-text search
- Robust replication

**Configuration Example**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'social_scheduler',
        'USER': 'dbuser',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

### MySQL 8+ (Alternative)

**Use If**:
- Organization already uses MySQL
- Team more familiar with MySQL
- Existing MySQL infrastructure

## Migration Path (SQLite → PostgreSQL)

### Step 1: Backup SQLite Data
```bash
python manage.py dumpdata > dump.json
```

### Step 2: Setup production database
```bash
createdb social_scheduler
```

### Step 3: Update Settings
```python
# Update DATABASES in settings.py
```

### Step 4: Run Migrations
```bash
python manage.py migrate
```

### Step 5: Load Data
```bash
python manage.py loaddata dump.json
```

### Step 6: Verify
```bash
python manage.py shell
>>> from posts.models import Post
>>> Post.objects.count()
```

## Related Decisions

- [ADR-001: 3-tier web application](ADR-001-architecture-decision.md)

## Notes

The choice of SQLite is **strictly for development and educational purposes**. The project's README and setup documentation explicitly state this limitation and provide migration guidance for production deployments.

**Evidence in Code**:
```python
# backend/home/settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

No environment variable configuration or production database settings are present, reinforcing the development-only nature of this setup.
