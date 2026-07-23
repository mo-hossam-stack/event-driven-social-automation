from django.contrib import admin

from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("content", "user", "share_on_linkedin", "updated_at")

    def get_list_display(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return [
                "content",
                "user",
                "share_on_linkedin",
                "shared_at_linkedin",
                "linkedin_post_urn",
                "updated_at",
            ]
        return ["content", "share_on_linkedin", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_readonly_fields(self, request, obj, *args, **kwargs):
        if obj and obj.shared_at_linkedin:
            return [
                "user",
                "content",
                "share_on_linkedin",
                "shared_at_linkedin",
                "linkedin_post_urn",
            ]
        if request.user.is_superuser:
            return ["shared_at_linkedin", "linkedin_post_urn"]
        return ["user", "shared_at_linkedin", "linkedin_post_urn"]

    def save_model(self, request, obj, form, change):
        if not change and not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Post, PostAdmin)