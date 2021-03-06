
DEBUG = True

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = 'LxBtzHQ5iO2OfbEkOooMZtsSYQedLsIUHssnSUSFv0L9LniJARNfD5QiEfk8C57KK0MtdTwjDhmubnoz'

SECRET_KEY = 'C3rqLiKpu2zhv6UH12b35yQi44Em23QJJ5XWlCQTxwv0iapG2vZDD0B063mjr1EFelKm8dEm4BugpN3G'

SECURITY_SALT = 'gHoY7DdRQ3sFl2u0Amu87TEMDo67NSgErMJ2qxyi6AQDF0zwQLi8kJuwHsbgxjC07qJxcLE4X4TPypz8'

#config for models.py
DB_NAME = 'programming_forum'
DB_USER = 'postgres'
DB_PASSWORD = 'no password'
DB_HOST = '127.0.0.1'
DB_PORT = '5432'

#only for debugging : disable caching
SEND_FILE_MAX_AGE_DEFAULT = 0

# Maximum data recieved should be less than 4MB
MAX_CONTENT_LENGTH = 4000000

IMG_UPLOADS_DIR = 'static/img/uploads'

BCRYPT_LOG_ROUNDS = 13

#Mail settings

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
# gmail authentication
MAIL_USERNAME = 'muchan.forum'
MAIL_PASSWORD = 'muchan12345678'
# mail accounts
MAIL_DEFAULT_SENDER = 'muchan.forum@gmail.com'

VERIFICATION_MAX_AGE = 60 * 60

PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 31 # a month
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
SESSION_USE_SIGNER = True

BOARDS = ['Python', 'Javascript', 'C++', 'C', #langs
          'Flask', 'Django', 'Rails', 'Express', #frameworks
           'Malware', '0 Days', 'Risk Management', 'Threat Intelligence', #cybersecurity
           'Compiler Design', 'Operating Systems', 'Artificial Intelligence', 'Mathematics' #Theory
           ]

MAX_THREADS_PER_PAGE = 10