from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = os.environ.get('DEBUG') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE') == 'True'

CORS_ORIGIN_WHITELIST = os.environ.get('CORS_ORIGIN_WHITELIST', '').split(',')
CORS_ORIGIN_ALLOW_ALL = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles"
]

ADDITIONAL_APPS = ['main']

THIRD_PARTY_APPS = ['rest_framework', 'corsheaders',]

INSTALLED_APPS += ADDITIONAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]

ROOT_URLCONF = "airquality.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "airquality.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static/')

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media/')


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# FORCE_SCRIPT_NAME = '/api'

POSTGRES_HOST=os.environ.get('POSTGRES_HOST')
POSTGRES_USER=os.environ.get('POSTGRES_USER')
POSTGRES_PASS=os.environ.get('POSTGRES_PASS')
POSTGRES_DB=os.environ.get('POSTGRES_DB')
POSTGRES_PORT=os.environ.get('POSTGRES_PORT')

PCD_POSTGRES_HOST=os.environ.get('PCD_POSTGRES_HOST')
PCD_POSTGRES_USER=os.environ.get('PCD_POSTGRES_USER')
PCD_POSTGRES_PASS=os.environ.get('PCD_POSTGRES_PASS')
PCD_POSTGRES_DB=os.environ.get('PCD_POSTGRES_DB')
PCD_POSTGRES_PORT=os.environ.get('PCD_POSTGRES_PORT')

THREDDS_WMS_URL=os.environ.get('THREDDS_WMS_URL')
THREDDS_CATALOG=os.environ.get('THREDDS_CATALOG')
THREDDS_OPANDAP=os.environ.get('THREDDS_OPANDAP')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': POSTGRES_DB,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASS,
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
    },
    'pcd_database': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': PCD_POSTGRES_DB,
        'USER': PCD_POSTGRES_USER,
        'PASSWORD': PCD_POSTGRES_PASS,
        'HOST': PCD_POSTGRES_HOST,
        'PORT': PCD_POSTGRES_PORT,
    },
}
