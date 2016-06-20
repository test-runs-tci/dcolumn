from .base import *

DEBUG = False

# Make data dir
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))
not os.path.isdir(DATA_DIR) and os.mkdir(DATA_DIR, 0o0775)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.abspath(os.path.join(
            BASE_DIR, '..', 'data', 'db.sqlite3')),
        }
    }


ALLOWED_HOSTS = [
    '127.0.0.1'
    ]

# email settings
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_REPLY_TO = 'donotreply@'

# Logging
LOG_ENV = 'travis'
EXAMPLES_LOG_FILE = '{}/{}-examples.log'.format(LOG_DIR, LOG_ENV)
DCOLUMNS_LOG_FILE = '{}/{}-dcolumn.log'.format(LOG_DIR, LOG_ENV)

LOGGING.get('handlers', {}).get(
    'examples_file', {})['filename'] = EXAMPLES_LOG_FILE
LOGGING.get('handlers', {}).get(
    'dcolumns_file', {})['filename'] = DCOLUMNS_LOG_FILE

LOGGING.get('loggers', {}).get('django.request', {})['level'] = 'DEBUG'
LOGGING.get('loggers', {}).get('examples', {})['level'] = 'DEBUG'
LOGGING.get('loggers', {}).get('dcolumns', {})['level'] = 'DEBUG'
