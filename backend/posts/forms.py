from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    share_now = forms.BooleanField(required=False)

    class Meta:
        model = Post
        fields = ["content", "share_on_linkedin", "share_now", "share_at"]

    share_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["share_on_linkedin"].initial = True
