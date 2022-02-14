import environ
from pathlib import Path
from .configuration import load_configuration


# set casting, default value
env = environ.Env(DEBUG=(bool, False))


# Read the .env file (development) or read the environment variables directly (production)
# TODO: Set default as False in production and export the environment variable
if env.bool('READ_DOT_ENV_FILE', default=True):
    environ.Env.read_env()


# TODO: Set to True by default in the DEVEL -> change when going to PROD
# Get the debug mode setting
# DEBUG = env('DEBUG')
DEBUG = True

# Get the secret key
SECRET_KEY = env('SECRET_KEY')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# TODO: Set to True by default in the DEVEL -> change when going to PROD
# Set the allowed hosts
ALLOWED_HOSTS = ['127.0.0.1']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party apps
    'crispy_forms',
    'crispy_tailwind',

    # Local apps
    'subjects'
]


# Middleware settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# URL settings
ROOT_URLCONF = 'app.urls'


# Templates settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# WSGI settings
WSGI_APPLICATION = 'app.wsgi.application'


# Database (https://docs.djangoproject.com/en/3.1/ref/settings/#databases)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT')
    }
}


# Cache (https://github.com/jazzband/django-redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
CACHE_TTL = 60 * 60  # 60 minutes


# Password validation (https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators)
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


# Internationalization (https://docs.djangoproject.com/en/3.1/topics/i18n/)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images; https://docs.djangoproject.com/en/3.1/howto/static-files/)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = 'static_root'
MEDIA_URL = '/media/'
MEDIA_ROOT = 'media_root'


# Auth settings
AUTH_USER_MODEL = 'subjects.User'


# E-mail settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Login/logout settings
LOGIN_REDIRECT_URL = '/subjects/'
LOGIN_URL = '/login'
LOGOUT_REDIRECT_URL = '/'


# Crispy forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'


# Predictor API settings
PREDICTOR_CONFIGURATION = load_configuration('predictor.json')


# Data settings
DATA_CONFIGURATION = load_configuration('data.json')


# Import settings
IMPORT_CONFIGURATION = load_configuration('import.json')


# # Logging settings
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'INFO',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose'
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler'
#         },
#
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.handlers.TimedRotatingFileHandler',
#             'filename': BASE_DIR / 'logs' / 'log.log',
#             'when': 'D',
#             'backupCount': 365,
#             'formatter': 'verbose'
#         }
#     },
#     'loggers': {
#         'dashboard': {
#             'handlers': ['console', 'mail_admins', 'file'],
#             'level': 'INFO'
#         },
#         'django': {
#             'handlers': ['console', 'file'],
#             'propagate': True,
#         },
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#     }
# }
