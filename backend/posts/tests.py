from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Post

User = get_user_model()


class PostViewTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="pw-alice-123")
        self.user_b = User.objects.create_user(username="bob", password="pw-bob-123")

    def make_post(self, user, content="hello world"):
        return Post.objects.create(
            user=user,
            content=content,
            share_now=True,
            share_on_linkedin=False,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("account_login")))

    def test_dashboard_lists_only_own_posts(self):
        self.make_post(self.user_a, content="alice private content")
        self.make_post(self.user_b, content="bob private content")
        self.client.force_login(self.user_a)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice private content")
        self.assertNotContains(response, "bob private content")

    def test_create_get_when_logged_in(self):
        self.client.force_login(self.user_a)
        response = self.client.get("/posts/create/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")
        self.assertContains(response, 'name="content"')

    def test_create_post_valid_data(self):
        self.client.force_login(self.user_a)

        response = self.client.post(
            "/posts/create/",
            {"content": "a brand new post", "share_now": "on"},
        )

        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.user, self.user_a)
        self.assertRedirects(response, f"/posts/{post.pk}/")
        self.assertEqual(response.url, reverse("posts:detail", kwargs={"pk": post.pk}))

    def test_create_post_invalid_data(self):
        self.client.force_login(self.user_a)

        response = self.client.post(
            "/posts/create/",
            {"content": "no schedule info"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_detail_scoped_to_owner(self):
        post_b = self.make_post(self.user_b, content="bob secret content")
        self.client.force_login(self.user_a)

        response = self.client.get(f"/posts/{post_b.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_detail_own_post(self):
        post_a = self.make_post(self.user_a, content="alice visible content")
        self.client.force_login(self.user_a)

        response = self.client.get(f"/posts/{post_a.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice visible content")

    def test_detail_requires_login(self):
        post_a = self.make_post(self.user_a)
        response = self.client.get(f"/posts/{post_a.pk}/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("account_login")))

    def test_create_requires_login(self):
        response = self.client.get("/posts/create/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("account_login")))
