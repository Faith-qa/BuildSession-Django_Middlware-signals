import time
from io import StringIO
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.http import JsonResponse
from django.urls import path
from django.contrib.auth.models import User
from django.conf import settings

#
# 1. Dummy Views (for testing)
#

def dummy_view(request):
    """A simple view returning JSON for testing."""
    return JsonResponse({"message": "Hello, World!"})

def error_view(request):
    """A view that raises an exception to test CustomExceptionHandlingMiddleware."""
    raise ValueError("Forced error for testing.")

urlpatterns = [
    path("dummy/", dummy_view, name="dummy"),
    path("error/", error_view, name="error"),
]


#
# 2. Base TestCase
#
@override_settings(ROOT_URLCONF=__name__)  # Use the local urlpatterns above
class MiddlewareTestCase(TestCase):
    """
    Base TestCase to set up dummy URLs and a test user.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_dummy_view(self):
        """
        Ensure the dummy view returns expected JSON and 200 status.
        """
        response = self.client.get("/dummy/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, World!"})


#
# 3. Tests for Each Middleware
#

#
# 3.1 PerformanceMonitoringMiddleware
#

@override_settings(MIDDLEWARE=[
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Our custom new-style middleware:
    "store.middleware.PerformanceMonitoringMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
])
class PerformanceMonitoringMiddlewareTest(MiddlewareTestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_performance_logged(self, mock_stdout):
        """
        Test that PerformanceMonitoringMiddleware prints timing info.
        """
        self.client.get("/dummy/")
        output = mock_stdout.getvalue()
        self.assertIn("PerformanceMonitor: /dummy/ took", output)


#
# 3.2 IPBlockingMiddleware
#

@override_settings(MIDDLEWARE=[
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Our custom new-style middleware:
    "store.middleware.IPBlockingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
])
class IPBlockingMiddlewareTest(MiddlewareTestCase):
    def test_blocked_ip(self):
        """
        Test that a blocked IP receives a 403 response.
        """
        # The middleware is hard-coded with BLOCKED_IPS = ['123.45.67.89']
        # (unless you changed it to read from settings)
        response = self.client.get("/dummy/", REMOTE_ADDR="123.45.67.89")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Your IP is blocked.", response.content)

    def test_allowed_ip(self):
        """
        Test that a non-blocked IP is allowed through.
        """
        response = self.client.get("/dummy/", REMOTE_ADDR="192.168.1.1")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"message": "Hello, World!"})


#
# 3.3 RateLimitingMiddleware
#

@override_settings(MIDDLEWARE=[
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Our custom new-style middleware:
    "store.middleware.RateLimitingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
])
class RateLimitingMiddlewareTest(MiddlewareTestCase):
    def setUp(self):
        super().setUp()
        from ..middleware import RateLimitingMiddleware
        # Clear or re-initialize the dictionary before each test
        RateLimitingMiddleware.request_log = {}
    def test_rate_limiting(self):
        """
        Test that exceeding MAX_REQUESTS triggers a 429 error.
        By default: MAX_REQUESTS=5 in the example.
        """
        # First 5 requests should be fine
        for i in range(5):
            response = self.client.get("/dummy/")
            self.assertEqual(response.status_code, 200, f"Request {i+1} was unexpectedly blocked")

        # 6th request should be rate-limited
        response = self.client.get("/dummy/")
        self.assertEqual(response.status_code, 429)
        self.assertIn(b"Rate limit exceeded. Try again later.", response.content)


#
# 3.4 UserActivityTrackingMiddleware
#

@override_settings(MIDDLEWARE=[
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Our custom new-style middleware:
    "store.middleware.UserActivityTrackingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
])
class UserActivityTrackingMiddlewareTest(MiddlewareTestCase):
    @patch("builtins.print")
    def test_unauthenticated_user_not_logged(self, mock_print):
        """
        Unauthenticated user requests should not log user ID info.
        """
        self.client.get("/dummy/")
        logs = [call_args[0][0] for call_args in mock_print.call_args_list]
        self.assertTrue(all("User " not in log for log in logs), "Expected no user logs for anonymous requests.")

    @patch("builtins.print")
    def test_authenticated_user_is_logged(self, mock_print):
        """
        Authenticated user requests should log user ID and action.
        """
        self.client.login(username='testuser', password='testpass')
        self.client.get("/dummy/")
        logs = [call_args[0][0] for call_args in mock_print.call_args_list]
        # Expect something like: "User 1 made a GET request to /dummy/, status=200"
        self.assertTrue(
            any("User 1 made a GET request to /dummy/, status=200" in log for log in logs),
            "Expected log with user activity not found."
        )


#
# 3.5 CustomExceptionHandlingMiddleware
#

