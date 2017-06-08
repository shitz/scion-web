# Copyright 2016 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Django settings for web_scion project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
from os.path import dirname as dir
from django.contrib import messages
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

WEB_SCION_DIR = dir(dir(dir(os.path.abspath(__file__))))
SCION_ROOT_DIR = dir(dir(WEB_SCION_DIR))
SCION_PYTHON_ROOT_DIR = os.path.join(SCION_ROOT_DIR, 'python')
sys.path.insert(0, WEB_SCION_DIR)
sys.path.insert(0, SCION_ROOT_DIR)
sys.path.insert(0, SCION_PYTHON_ROOT_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

LOG_DIR = os.path.join(WEB_SCION_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'ad_manager',
    'guardian',

    # Two-factor authentication
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Two-factor authentication
    'django_otp.middleware.OTPMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)

ROOT_URLCONF = 'web_scion.urls'

WSGI_APPLICATION = 'web_scion.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'ad_manager.context_processors.account_urls',
)


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

# For django-guardian
ANONYMOUS_USER_ID = -1

ENABLED_2FA = False

# 2FA options
TWO_FACTOR_PATCH_ADMIN = ENABLED_2FA

# Security settings
CSRF_COOKIE_HTTPONLY = True

# configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'scion-web.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}
