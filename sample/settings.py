from os import environ

from django.core.management.utils import get_random_secret_key


SECRET_KEY = environ.get("DJANGO_SECRET_KEY") or get_random_secret_key()
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "django"]
ROOT_URLCONF = "sample.urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
X_FRAME_OPTIONS = "DENY"
