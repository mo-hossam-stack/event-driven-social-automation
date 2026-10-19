from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("posts/create/", views.PostCreateView.as_view(), name="create"),
    path("posts/<int:pk>/", views.PostDetailView.as_view(), name="detail"),
]
