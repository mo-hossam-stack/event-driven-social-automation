import logging
from datetime import datetime

import inngest
from django.utils import timezone

from helpers.linkedin import LinkedInShareError, share_to_linkedin
from posts.models import Post

from .client import inngest_client

logger = logging.getLogger(__name__)

# Create an Inngest function

@inngest_client.create_function(
    fn_id="post_scheduler",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="posts/post.scheduled"),
    retries=3,
)
def post_scheduler(ctx: inngest.ContextSync) -> str:
    post_id = ctx.event.data["post_id"]

    logger.info(
        "Workflow started (post=%s, run_id=%s, attempt=%s)",
        post_id,
        ctx.run_id,
        ctx.attempt,
    )

    # Step 1: Fetch post — memoized after first success
    post_data = ctx.step.run("fetch-post", lambda: _fetch_post(post_id))

    # Guard: exit early if already completed (handles duplicate events)
    if post_data["share_complete_at"] is not None:
        logger.info("Post %s already completed, skipping", post_id)
        return "already-completed"

    # Step 2: Sleep until scheduled time
    share_at = datetime.fromisoformat(post_data["share_at"])
    ctx.step.sleep_until("wait-for-schedule", share_at)

    # Step 3: Record workflow start (AFTER sleep — timestamps reflect execution)
    ctx.step.run("record-start", lambda: _record_start(post_id))

    # Step 4: Share to LinkedIn
    ctx.step.run("linkedin-share", lambda: _share_to_linkedin(post_id))

    # Step 5: Record workflow completion
    ctx.step.run("record-completion", lambda: _record_completion(post_id))

    logger.info("Workflow completed (post=%s)", post_id)
    return "done"




def _fetch_post(post_id: int) -> dict:
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        raise inngest.NonRetriableError(f"Post {post_id} no longer exists")

    return {
        "id": post.id,
        "share_at": post.share_at.isoformat() if post.share_at else None,
        "share_complete_at": (
            post.share_complete_at.isoformat()
            if post.share_complete_at
            else None
        ),
    }


def _record_start(post_id: int) -> None:
    Post.objects.filter(id=post_id).update(share_start_at=timezone.now())
    logger.info("Recorded share_start_at (post=%s)", post_id)


def _share_to_linkedin(post_id: int) -> None:
    post = Post.objects.get(id=post_id)

    # Idempotency guard: skip if already shared
    if post.shared_at_linkedin:
        logger.warning(
            "Post %s already shared (urn=%s), skipping",
            post_id,
            post.linkedin_post_urn,
        )
        return

    try:
        post_urn = share_to_linkedin(post.user, post.content)
    except LinkedInShareError:
        logger.exception("LinkedIn API error (post=%s)", post_id)
        raise
    except Exception:
        logger.exception("Unexpected error sharing post %s", post_id)
        raise

    # Single update — URN + timestamp together
    Post.objects.filter(id=post_id).update(
        shared_at_linkedin=timezone.now(),
        linkedin_post_urn=post_urn,
    )
    logger.info("Post %s shared to LinkedIn (urn=%s)", post_id, post_urn)


def _record_completion(post_id: int) -> None:
    Post.objects.filter(id=post_id).update(share_complete_at=timezone.now())
    logger.info("Recorded share_complete_at (post=%s)", post_id)
