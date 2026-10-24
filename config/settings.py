import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "planner",
]

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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---- Database ----
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Non-manifest storage: works without running collectstatic in dev/tests.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Auth redirects ----
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "saved_trips"
LOGOUT_REDIRECT_URL = "home"

# Map Django message levels to Bootstrap alert classes.
MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

# ---- Cache (local dev; swap for Redis/memcached in production) ----
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "travelmate-cache",
    }
}

# ---- Email (console backend: password-reset emails print to the terminal) ----
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---- Security (activates when DEBUG is off) ----
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    if env_bool("DJANGO_SECURE_SSL", False):
        SECURE_SSL_REDIRECT = True
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---- App-specific config ----
TRAVELMATE = {
    "AI_PROVIDER": os.getenv("AI_PROVIDER", "fallback").strip().lower(),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "").strip(),
    "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
    "USER_AGENT": os.getenv("APP_USER_AGENT", "AI-TravelMate/1.0"),
    "NOMINATIM_BASE_URL": os.getenv(
        "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
    ),
    "OVERPASS_URL": os.getenv(
        "OVERPASS_URL", "https://overpass-api.de/api/interpreter"
    ),
    "OPEN_METEO_URL": os.getenv(
        "OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast"
    ),
    "HTTP_TIMEOUT": int(os.getenv("HTTP_TIMEOUT", "15")),
    "CACHE_TTL_GEOCODE": int(os.getenv("CACHE_TTL_GEOCODE", "604800")),
    "CACHE_TTL_PLACES": int(os.getenv("CACHE_TTL_PLACES", "86400")),
    "CACHE_TTL_WEATHER": int(os.getenv("CACHE_TTL_WEATHER", "3600")),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"planner": {"handlers": ["console"], "level": "INFO"}},
}

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"