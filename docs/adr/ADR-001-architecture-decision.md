# ADR-001: Monolithic Django Architecture

**Status**: Accepted

**Date**: 2/2026

**Decision Makers**: Project author (Mohamed Hossam)

## Context

The project needs to demonstrate scheduled social media posting to LinkedIn with the following requirements:
- User authentication and OAuth integration
- Post scheduling and delayed execution  
- Integration with LinkedIn API
- personal project purpose
- Minimal operational complexity
- Fast development time

**Alternatives Considered**:
1. **Monolithic Django Application** (Django + Inngest)
2. **3-Tier Web Application** (Django + Inngest + React) (chosen)
3. **Microservices Architecture** (Django API + separate scheduler service)
4. **Serverless Architecture** (AWS Lambda + Step Functions)

## Decision

We will use a **3-tier web application** (Django + Inngest + React) for workflow orchestration.

## Rationale

### Chosen Approach: 3-Tier Web Application (Django + Inngest + React)

**Advantages**:
- ✅ Simple deployment (single application)
- ✅ Built-in admin interface for post management
- ✅ django-allauth provides OAuth integration
- ✅ Inngest eliminates need for Redis/RabbitMQ/Celery
- ✅ Minimal infrastructure requirements
- ✅ Easy to understand for tutorial audience
- ✅ Rapid development

**Disadvantages**:
- ❌ Cannot scale components independently
- ❌ All code in single repository
- ❌ Tight coupling between components
- ❌ Harder to add new platforms later (must modify core app)

### Alternative 1: Microservices

**Why Not Chosen**:
- Excessive complexity for personal project
- Requires service discovery, API gateway
- Multiple deployments to manage
- Overkill for single-platform (LinkedIn) support

### Alternative 2: Serverless

**Why Not Chosen**:
- Vendor lock-in (AWS or GCP)
- Requires cloud account for tutorials
- More complex for students to run locally
- Higher learning curve

### Alternative 3: Django + Celery

**Why Not Chosen**:
- Requires Redis or RabbitMQ installation
- More complex local setup
- Inngest provides simpler developer experience
- Celery adds operational overhead

## Consequences

### Positive

- Simple local development setup
- Single codebase easy to navigate
- Django admin provides instant UI
- Inngest handles workflow reliability
- Tutorial is accessible to Django beginners

### Negative

- Limited scalability (SQLite, single instance)
- Adding new social platforms requires core changes
- Cannot scale scheduling independently from web server
- Production deployment requires significant changes

### Mitigation

For production use, recommend:
- Migrate to PostgreSQL
- Deploy multiple Django instances behind load balancer
- Use Inngest Cloud for workflow execution
- Consider extracting LinkedIn integration to separate service

## Related Decisions

- [ADR-002: SQLite Database Choice](ADR-002-database-choice.md)
- [ADR-003: OAuth Authentication Strategy](ADR-003-auth-strategy.md)
- [ADR-004 :inngest-scheduler ](ADR-004-inngest-scheduler.md)

## Notes

This architecture is **intentionally simplified** for educational purposes. It demonstrates core concepts without the operational complexity of production-grade systems.

The tutorial focuses on:
1. OAuth integration patterns
2. Event-driven workflow orchestration
3. External API integration

Not on:
- Microservices design
- High availability
- Horizontal scaling
- Production deployment
