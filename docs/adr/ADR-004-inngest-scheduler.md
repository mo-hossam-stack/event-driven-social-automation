# ADR-004: Inngest for Task Scheduling

**Status**: Accepted

**Date**: 2024 (inferred from project creation)

**Decision Makers**: Mohamed Hossam

## Context

The application needs to execute scheduled tasks (publishing posts at specific times). This requires:
- Time-delayed execution (schedule post for future publication)
- Reliable execution (guarantees post will publish)
- Workflow orchestration (multi-step operations)
- Error handling and retries
- Development-friendly setup

**Requirements**:
- Schedule tasks for arbitrary future times
- Guarantee at-least-once execution
- Handle failures gracefully with retries
- Support multi-step workflows
- Simple local development setup
- Observable (workflow execution history)

**Alternatives Considered**:
1. **Inngest** (chosen)
2. **Celery + Redis/RabbitMQ**
3. **Django-Q**
4. **APScheduler**
5. **Cloud-based (AWS Step Functions, Google Cloud Tasks)**
6. **Cron jobs**

## Decision

Use **Inngest** as the task scheduling and workflow orchestration engine.

## Rationale

### Chosen Approach: Inngest

**Advantages**:
- ✅ Zero infrastructure dependencies (dev: Docker, prod: Cloud)
- ✅ Built-in workflow orchestration (`ctx.step.sleep_until()`)
- ✅ Automatic retries with exponential backoff
- ✅ Event-driven architecture
- ✅ Workflow execution history and observability
- ✅ Idempotency via event IDs
- ✅ Easy local development (Inngest dev server)
- ✅ Simple SDK integration
- ✅ Managed service (Inngest Cloud) for production
- ✅ No separate worker management required

**Disadvantages**:
- ❌ External dependency (vendor lock-in)
- ❌ Less established than Celery
- ❌ Requires internet connection (production mode)
- ❌ Newer technology (smaller community)
- ❌ Pricing model for scale (though has generous free tier)

**Configuration**:
```python
# scheduler/client.py
from inngest import Inngest

inngest_client = Inngest(
    app_id="social_share",
    logger=gunicorn_logger
)
```

### Alternative 1: Celery + Redis/RabbitMQ

**Why Not Chosen**:
- Requires Redis or RabbitMQ installation (complex local setup)
- Must manage separate worker processes
- More operational overhead (queue monitoring, worker management)
- Students must install and configure message broker
- No built-in workflow UI/dashboard

**Complexity Comparison**:
```
Inngest Setup:
1. docker compose up inngest
2. Run Django server
❱ Total: 2 steps

Celery Setup:
1. Install Redis
2. Configure Celery settings
3. Start Redis server
4. Start Celery worker
5. Start Celery beat (for periodic tasks)
6. Run Django server
❱ Total: 6 steps
```

**Code Comparison**:

*Inngest*:
```python
@inngest_client.create_function(
    fn_id="post_scheduler",
    trigger=inngest.TriggerEvent(event="posts/post.scheduled"),
)
def post_scheduler(ctx: inngest.Context):
    ctx.step.sleep_until("wait", publish_date)
    ctx.step.run("publish", lambda: publish_to_linkedin(post))
```

*Celery*:
```python
@shared_task
def publish_post(post_id):
    publish_to_linkedin(post_id)

# In view/model:
from django_celery_beat.models import PeriodicTask
publish_post.apply_async(args=[post.id], eta=publish_date)
```
→ Also requires django-celery-beat for scheduled tasks

### Alternative 2: Django-Q

**Why Not Chosen**:
- Still requires Redis or message broker
- Less mature than Celery
- Limited workflow orchestration features
- No built-in retry logic for complex workflows

### Alternative 3: APScheduler

**Why Not Chosen**:
- In-process scheduler (not distributed)
- Jobs lost on server restart
- No persistence layer
- Not suitable for production
- No workflow orchestration

### Alternative 4: Cloud Services (AWS Step Functions, Cloud Tasks)

**Why Not Chosen**:
- Requires cloud account
- Vendor lock-in (AWS/GCP)
- Cannot run locally without cloud credentials
- More complex for students to set up
- Costs money at scale

### Alternative 5: Cron Jobs

**Why Not Chosen**:
- Fixed schedule only (not arbitrary future times)
- No sub-minute granularity
- Must poll database for pending posts
- Inefficient (checking every minute vs event-driven)
- No workflow orchestration or retries

## Implementation Details

### Workflow Function

```python
@inngest_client.create_function(
    fn_id="post_scheduler",
    trigger=inngest.TriggerEvent(event="posts/post.scheduled"),
)
def post_scheduler(ctx: inngest.Context) -> str:
    # Step 1: Get post from database
    instance = ctx.step.run("fetch-post", lambda: Post.objects.get(id=object_id))
    
    # Step 2: Record workflow start
    start_at = ctx.step.run("workflow-start", get_now)
    qs.update(share_start_at=start_at)
    
    # Step 3: Sleep until scheduled time
    ctx.step.sleep_until("linkedin-sleeper-schedule", publish_date)
    
    # Step 4: Publish to LinkedIn
    ctx.step.run("linkedin-share-workflow-step", 
                 lambda: workflow_share_on_linkedin_node(instance))
    
    # Step 5: Record workflow end
    end_at = ctx.step.run("workflow-end", get_now)
    qs.update(share_complete_at=end_at)
    
    return "done"
```

### Event Triggering

```python
# In Post.save()
inngest_client.send_sync(
    inngest.Event(
        name="posts/post.scheduled",
        id=f"posts/post.scheduled.{self.id}",
        data={"object_id": self.id}
    )
)
```

### Development Setup

**Docker Compose** (`compose.yaml`):
```yaml
services:
  inngest:
    image: inngest/inngest:latest
    ports:
      - "8288:8288"
    command: inngest dev
```

**Environment**:
```bash
INNGEST_DEV=1  # Use local dev server
```

**Access Dashboard**: http://localhost:8288/

### Production Setup

**Environment**:
```bash
INNGEST_EVENT_KEY=<key>
INNGEST_SIGNING_KEY=<key>
INNGEST_SIGNING_KEY_FALLBACK=<key>
```

**Deployment**:
- Django app exposes `/api/inngest` webhook
- Inngest Cloud calls webhook to execute workflows
- No separate worker processes needed

## Consequences

### Positive

- Extremely simple local setup (one Docker command)
- Visual workflow dashboard out of the box
- Automatic retry and error handling
- Event-driven architecture encourages decoupling
- No background worker processes to manage
- Production deployment simpler (Inngest Cloud is managed)
- Built-in observability (workflow execution logs)

### Negative

- Vendor dependency on Inngest
- Newer technology (less Stack Overflow answers)
- Requires internet connectivity for production
- Migration to different system would require code changes
- Free tier limits (though generous for small projects)

### Operational Impact

**Development**:
- No breaking: Docker Compose handles Inngest dev server
- Dashboard at localhost:8288 for debugging

**Production**:
- Must configure Inngest Cloud account
- Webhook endpoint must be publicly accessible
- Network egress from Inngest Cloud to application
- Potential latency (external service call)

### Cost Considerations

**Inngest Cloud Pricing** (as of 2024):
- Free tier: 100,000 steps/month
- Paid: $0.001 per step after free tier

**Example**:
- 10,000 posts/month
- 5 steps per post → 50,000 steps
- **Cost**: $0 (within free tier)

**At Scale** (100,000 posts/month, 5 steps each):
- 500,000 steps/month
- **Cost**: ~$400/month

**Celery Equivalent Cost**:
- Redis instance: ~$15-50/month (AWS ElastiCache)
- Worker EC2 instances: ~$50-200/month
- Operational overhead: Engineering time

### Migration Path (If Needed)

**To Celery**:
1. Install Celery + Redis
2. Convert Inngest functions to Celery tasks
3. Replace `inngest_client.send_sync()` with `task.apply_async()`
4. Implement retry logic manually
5. Estimated effort: 2-3 days

**To Cloud Tasks (GCP)**:
1. Create Cloud Tasks queue
2. Convert workflow to HTTP task handler
3. Schedule tasks with `create_task()` API
4. Handle retries via Cloud Tasks configuration
5. Estimated effort: 3-5 days

## Monitoring and Observability

**Inngest Dashboard Provides**:
- Workflow execution history
- Failed workflow details
- Retry attempts and timing
- Step-by-step execution logs
- Event publishing history

**Celery Equivalent** would require:
- Flower (monitoring tool)
- Custom logging
- Error tracking integration (Sentry)

## Related Decisions

- [ADR-001: 3-tier web application](ADR-001-architecture-decision.md)

## Notes

Inngest was specifically chosen to **reduce operational complexity** for an educational project. The primary goal was to demonstrate event-driven scheduling without the overhead of traditional job queues.

The decision prioritizes:
1. **Developer experience** (easy local setup)
2. **Reliability** (automatic retries)
3. **Observability** (built-in dashboard)

Over:
1. Technology maturity
2. Community size
3. Self-hosted infrastructure

**For production use**, evaluate:
- Workflow volume and cost
- Vendor lock-in tolerance
- Team familiarity with event-driven patterns
- Requirement for self-hosted infrastructure

If self-hosting is critical, Celery + Redis is the recommended alternative.
