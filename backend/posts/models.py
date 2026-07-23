import logging
import inngest
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from helpers import linkedin
from scheduler.client import inngest_client

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    share_now = models.BooleanField(default=None, null=True, blank=True)
    share_at = models.DateTimeField(null=True, blank=True)
    share_start_at = models.DateTimeField(null=True, blank=True)
    share_complete_at = models.DateTimeField(null=True, blank=True)
    share_on_linkedin = models.BooleanField(default=False)
    shared_at_linkedin = models.DateTimeField(null=True, blank=True)
    linkedin_post_urn = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post #{self.pk} by {self.user_id}"

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        if self.share_now is None and self.share_at is None:
            raise ValidationError(
                {
                    "share_at": "You must select a time to share or share it now.",
                    "share_now": "You must select a time to share or share it now.",
                }
            )
        if self.share_on_linkedin:
            self.verify_can_share_on_linkedin()
        # run the save method (pre & post save)

    def get_scheduled_platforms(self):
        platforms = []
        if self.share_on_linkedin:
            platforms.append("linkedin")
        return platforms


    def save(self, *args, **kwargs):
        creating = self.pk is None

        should_schedule = (
            creating
            and self.share_on_linkedin
            and (self.share_now is True or self.share_at is not None)
        )

        if self.share_now:
            self.share_at = timezone.now()
        super().save(*args, **kwargs)

        if should_schedule:
            logger.info(
                "Scheduling post %s for user %s (share_at=%s)",
                self.id,
                self.user_id,
                self.share_at,
            )
            inngest_client.send_sync(
                inngest.Event(
                    name="posts/post.scheduled",
                    id=f"posts/post.scheduled.{self.id}",
                    data={"post_id": self.id},
                )
            )

    
    def verify_can_share_on_linkedin(self):
        # run validation errors if attempting to share on linkedin
        if len(self.content) < 5:
            raise ValidationError({
                "content": "Content must be at least 5 characters long."
            })
        if self.shared_at_linkedin:
            raise ValidationError({
                "share_on_linkedin": f"Content is already shared on LinkedIn at {self.shared_at_linkedin}.",
                "content": "Content is already shared on LinkedIn."
            })
        try:
            linkedin.get_linkedin_user_details(self.user)
        except linkedin.UserNotConnectedLinkedIn:
            raise ValidationError({
                "user": f"You must connect LinkedIn before sharing to LinkedIn."
            })
        except Exception as e:
            raise ValidationError({
                "user": f"{e}"
            })