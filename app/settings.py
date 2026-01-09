from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ac!=&=@^2a)@v-2e_h5x7znxt(2@1ht#!fjs*8%p(dh6%kzm%@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.18.25",
    "192.168.100.151",
]

# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "corsheaders",
    "core",
    "records",
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True 

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Patch para soportar MariaDB 10.4 (solo para desarrollo)
from django.db.backends.base import base

def check_database_version_supported_patch(self):
    """Deshabilitar verificación de versión de base de datos"""
    pass

# Monkey patch para permitir MariaDB 10.4 con Django 5.2
base.BaseDatabaseWrapper.check_database_version_supported = check_database_version_supported_patch  # type: ignore[method-assign]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "mucosa_db",
        "USER": "root", 
        "PASSWORD": "", 
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        # Forzar compatibilidad con MariaDB 10.4 (temporal)
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS += ["storages"]


USE_S3 = False # cambia a False en DEV si quieres FS local
if USE_S3:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_ENDPOINT_URL = "http://127.0.0.1:9000" # MinIO local
    AWS_ACCESS_KEY_ID = "minioadmin"
    AWS_SECRET_ACCESS_KEY = "minioadmin"
    AWS_STORAGE_BUCKET_NAME = "mucosa-media"
    AWS_S3_REGION_NAME = "us-east-1"
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_FILE_OVERWRITE = False
else:
    # Django 5 STORAGES (FS local)
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        # Logger propio de tu app:
        "records": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Si quieres ver SQL en consola mientras depuras, descomenta:
        # "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'