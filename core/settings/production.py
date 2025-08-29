from .base import * # noqa: F403
import django_on_heroku # Configure Django App for Heroku.
import os

# Application definition

ALLOWED_HOSTS = ['https://limitless-basin-36434-9b35839c4566.herokuapp.com/', 'https://www.shotgeek.com', 'http://127.0.0.1:8000', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://limitless-basin-36434-9b35839c4566.herokuapp.com', 'https://www.shotgeek.com', 'http://127.0.0.1:8000']

DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),  # Default PostgreSQL port
    }
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

WHITENOISE_KEEP_ONLY_HASHED_FILES = True


STATIC_DIR = os.path.join(BASE_DIR, 'static') # noqa: F405

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles") # noqa: F405

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
MEDIA_URL = '/media/'
STATICFILES_DIRS = [
    STATIC_DIR,
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media') # noqa: F405


django_on_heroku.settings(locals())
