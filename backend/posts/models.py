from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL



class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    share_now = models.BooleanField(default=None, null=True, blank=True)
    share_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    share_start_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    share_complete_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    share_on_linkedin = models.BooleanField(default=False)
    shared_at_linkedin = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)