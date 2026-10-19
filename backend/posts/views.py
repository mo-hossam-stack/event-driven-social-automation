from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from .forms import PostForm
from .models import Post


class DashboardView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "posts/dashboard.html"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Post created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("posts:detail", kwargs={"pk": self.object.pk})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)
