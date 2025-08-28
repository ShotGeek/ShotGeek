from .base import *

ALLOWED_HOSTS = ['*']

DEBUG=True

# Use PostgreSQL when in Docker environment, otherwise use SQLite
import os
if os.environ.get('DOCKER_ENV'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'shotgeek',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }

# In development, use WhiteNoise but with no caching and auto-refresh,
# so static changes are reflected immediately. We keep WhiteNoise entries
# from base INSTALLED_APPS and MIDDLEWARE unchanged.

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_DIR = os.path.join(BASE_DIR, 'static')

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
MEDIA_URL = '/media/'
STATICFILES_DIRS = [
    STATIC_DIR,
]

# WhiteNoise dev configuration: auto-refresh and (optionally) no-cache
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 0

# Use manifest storage so URLs include a hash (fingerprint). This provides
# reliable cache-busting in the browser when static files change.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')