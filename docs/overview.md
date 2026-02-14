# Project Overview

## Executive Summary

**Social Share Scheduler** is a Django-based web application that enables authenticated users to schedule and automatically publish posts to LinkedIn. The system leverages OAuth 2.0 for secure LinkedIn account integration and uses Inngest, an event-driven workflow engine, to handle reliable task scheduling and execution.

## Problem Statement

Sharing content on social media platforms like LinkedIn is straightforward through their APIs, but reliably scheduling posts for future publication presents significant challenges:

1. **Scheduling Complexity** - Traditional Django-only solutions require complex job queue infrastructure (Celery, Redis, RabbitMQ)
2. **Reliability** - Ensuring scheduled tasks execute even if the application restarts or crashes
3. **OAuth Token Management** - Securely storing and refreshing user access tokens
4. **Multi-Platform Extensibility** - Building a system that can easily extend to other social platforms

## Solution Approach

This project demonstrates a modern, simplified approach to social media scheduling by combining:

- **Django + django-allauth** - Handles user authentication and OAuth flows with LinkedIn
- **Inngest** - Provides reliable, event-driven task scheduling without traditional job queue infrastructure
- **LinkedIn API v2** - Publishes user-generated content to LinkedIn profiles

## Core Capabilities

### 1. LinkedIn OAuth Integration
- Users authenticate via "Login with LinkedIn" using OpenID Connect
- Access tokens are securely stored in the database via django-allauth
- Token validation ensures users maintain valid LinkedIn connections

### 2. Post Scheduling
- Users create posts through Django admin interface
- Posts can be scheduled for immediate or future publication
- Scheduling triggers Inngest workflow events
- Workflows handle delayed execution and LinkedIn API calls

### 3. Admin Interface
- Custom Django admin for post management
- User-scoped post visibility (non-superusers see only their posts)
- Read-only fields for published posts to prevent accidental modifications
- Validation prevents deletion of already-published content

## Architecture Style

**3-Tier Web Application** with event-driven task processing:

- Presentation Tier: Django admin interface (frontend in the future)
- Logic Tier: Django application logic
- Data Tier: Database (SQLite for development)

## Key Components

### Django Applications

| Application | Purpose |
|-------------|---------|
| `home` | Main Django project configuration and settings |
| `posts` | Post model, admin interface, and business logic |
| `scheduler` | Inngest client, workflow functions, and event handling |
| `helpers` | LinkedIn API integration utilities |

### External Services

| Service | Role |
|---------|------|
| LinkedIn OAuth | User authentication and authorization |
| LinkedIn API v2 | Post publishing endpoint |
| Inngest | Workflow orchestration and scheduling |

## Data Flow

### Post Creation Flow
1. User logs into Django admin (frontend in the future)
2. User creates a new Post with content and schedule time
3. Post model validation checks LinkedIn connection
4. Post is saved to database
5. Post save signal triggers Inngest event
6. Inngest schedules workflow for execution

### Post Publishing Flow
1. Inngest workflow wakes at scheduled time
2. Workflow retrieves Post from database
3. Workflow validates LinkedIn connection
4. Workflow calls LinkedIn API with user's access token
5. Post is published to LinkedIn
6. Database updated with publication timestamp
7. Workflow completes

## Technology Stack

### Backend
- **Python 3.8+** - Programming language
- **Django 4.2+** - Web framework
- **django-allauth** - OAuth authentication library
- **python-dotenv** - Environment variable management

### Task Scheduling
- **Inngest** - Event-driven workflow engine
- **Docker** - Inngest server containerization

### Development Tools
- **Jupyter** - Interactive development and testing via notebooks
- **rav** - Script runner for common development tasks

### Database
- **SQLite** - Development database (file-based)
- **PostgreSQL** - Production database 
- **Django ORM** - Database abstraction layer

## Project Structure

```
Social-Share-Scheduler/
├── backend/                          # Django application source code
│   ├── home/                  # Main Django project
│   │   ├── settings.py           # Configuration
│   │   ├── urls.py               # URL routing
│   │   └── wsgi.py               # WSGI entry point
│   ├── posts/                    # Posts application
│   │   ├── models.py             # Post model
│   │   ├── admin.py              # Admin interface
│   │   └── migrations/           # Database migrations
│   ├── scheduler/                # Inngest integration
│   │   ├── client.py             # Inngest client setup
│   │   ├── functions.py          # Workflow definitions
│   │   └── views.py              # Inngest endpoint
│   └── helpers/                  # Utility modules
│       └── linkedin.py           # LinkedIn API helpers
├── notebooks/                    # Jupyter notebooks for development
│   ├── setup.py                  # Django initialization for notebooks
│   └── *.ipynb                   # Development notebooks
├── docs/                         # Documentation (this directory)
├── compose.yaml                  # Docker Compose for Inngest
├── requirements.txt              # Python dependencies
├── rav.yaml                      # Development scripts
└── .env.prod.sample              # Environment variable template
```

## Development Workflow

### Local Development
1. Activate virtual environment
2. Start Inngest server via Docker Compose
3. Run Django development server
4. Access admin at `http://localhost:8000/admin/`
5. Inngest dashboard at `http://localhost:8288/`

### Notebook-Driven Development
The project includes Jupyter notebooks for:
- Testing LinkedIn API integration
- Exploring django-allauth token storage
- Triggering Inngest functions manually
- Developing helper functions interactively

### Script Automation
The `rav.yaml` file defines common development tasks:
- `rav run notebook` - Start Jupyter notebook server
- `rav run server` - Start Django development server
- `rav run scheduler_server` - Start Inngest via Docker
- `rav run scheduler_server_down` - Stop Inngest containers

## Configuration

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `INNGEST_EVENT_KEY` | Inngest event authentication | Production only |
| `INNGEST_SIGNING_KEY` | Inngest request signing | Production only |
| `INNGEST_SIGNING_KEY_FALLBACK` | Key rotation support | Production only |
| `DJANGO_SETTINGS_MODULE` | Django settings module | Auto-set |
| `INNGEST_DEV` | Enable Inngest dev mode | Development only |

### LinkedIn OAuth Configuration

LinkedIn OAuth is configured via Django admin interface:
- Provider: `openid_connect`
- Provider ID: `linkedin`
- Scopes: `openid`, `profile`, `w_member_social`, `email`
- Server URL: `https://www.linkedin.com/oauth`

> **Note**: The `settings.py` file contains commented-out configuration showing the structure. In practice, this is configured through the Django admin UI after creating a LinkedIn Developer App.

## Current Limitations

### Development-Focused
- Hardcoded `SECRET_KEY` in settings (insecure for production)
- `DEBUG = True` enabled
- SQLite database (not suitable for production concurrency)
- No production-grade logging or monitoring
- No automated tests

### Feature Limitations
- LinkedIn-only (no other platforms)
- No post editing after scheduling
- No post preview functionality
- No media attachments (text-only posts)
- No post analytics or engagement tracking

### Security Considerations
- Broad `ALLOWED_HOSTS = ['*']` in debug mode
- No rate limiting on API endpoints
- No CSRF exemptions for Inngest webhook (relies on Inngest signing)
- Access tokens stored in plaintext in database

## Deployment Considerations

### Not Production-Ready

This project is designed as an educational tutorial and requires significant hardening for production use:

1. **Security** - Environment-based secrets, secure token storage, rate limiting
2. **Database** - PostgreSQL or MySQL with proper connection pooling
3. **Logging** - Structured logging with centralized aggregation
4. **Monitoring** - Application performance monitoring, error tracking
5. **Testing** - Unit tests, integration tests, end-to-end tests
6. **Infrastructure** - Load balancing, auto-scaling, health checks

## Learning Objectives

This project demonstrates:
- OAuth 2.0 integration with third-party platforms
- Event-driven architecture patterns
- Workflow orchestration with Inngest
- Django admin customization
- Model validation and business logic
- External API integration
- Docker containerization basics

## Related Resources

- [LinkedIn API Documentation](https://docs.microsoft.com/en-us/linkedin/)
- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Inngest Documentation](https://www.inngest.com/docs)
