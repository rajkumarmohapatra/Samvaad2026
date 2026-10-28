import os,sys
from pathlib import Path
import dj_database_url
BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.getenv('DEBUG','false').lower()=='true'
SECRET_KEY=os.environ.get('SECRET_KEY','')
if not SECRET_KEY:
    if DEBUG or os.getenv('TESTING')=='1': SECRET_KEY='local-tests-only-not-a-production-secret'
    else: raise RuntimeError('Set SECRET_KEY in the hosting secret store before starting the portal.')
ALLOWED_HOSTS=[x.strip() for x in os.getenv('ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',') if x.strip()]
if os.getenv('RENDER_EXTERNAL_HOSTNAME'): ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
CSRF_TRUSTED_ORIGINS=[x for x in os.getenv('CSRF_TRUSTED_ORIGINS','').split(',') if x]
if os.getenv('RENDER_EXTERNAL_HOSTNAME'): CSRF_TRUSTED_ORIGINS.append('https://'+os.environ['RENDER_EXTERNAL_HOSTNAME'])
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','operations']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','operations.middleware.PrivateResponseMiddleware','operations.middleware.RequestActivityMiddleware']
ROOT_URLCONF='samvaad.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','operations.context.common']}}]
WSGI_APPLICATION='samvaad.wsgi.application'
db_url=os.getenv('DATABASE_URL_UNPOOLED') if 'migrate' in sys.argv else os.getenv('DATABASE_URL')
if not db_url and not DEBUG and os.getenv('TESTING')!='1':raise RuntimeError('Production requires a persistent PostgreSQL DATABASE_URL; ephemeral SQLite is not allowed.')
DATABASES={'default':dj_database_url.parse(db_url or 'sqlite:///'+str(BASE_DIR/'local.sqlite3'),conn_max_age=60,conn_health_checks=True)}
if db_url and not DEBUG and os.getenv('TESTING')!='1' and DATABASES['default']['ENGINE']!='django.db.backends.postgresql':raise RuntimeError('Production database must be PostgreSQL.')
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='en-in';TIME_ZONE='Asia/Kolkata';USE_I18N=True;USE_TZ=True
STATIC_URL='/static/';STATIC_ROOT=BASE_DIR/'staticfiles';STATICFILES_DIRS=[BASE_DIR/'static']
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
LOGIN_URL='login';LOGIN_REDIRECT_URL='dashboard';LOGOUT_REDIRECT_URL='login'
SESSION_COOKIE_HTTPONLY=True;SESSION_COOKIE_SAMESITE='Lax';SESSION_COOKIE_AGE=28800
SESSION_COOKIE_SECURE=not DEBUG and os.getenv('TESTING')!='1';CSRF_COOKIE_SECURE=SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT=SESSION_COOKIE_SECURE;SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_SECONDS=31536000 if SESSION_COOKIE_SECURE else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False;SECURE_HSTS_PRELOAD=False
SECURE_CONTENT_TYPE_NOSNIFF=True;X_FRAME_OPTIONS='DENY'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE=3_000_000
FILE_UPLOAD_MAX_MEMORY_SIZE=3_000_000
FIELD_ENCRYPTION_KEY=os.getenv('FIELD_ENCRYPTION_KEY','')
BOOTSTRAP_TOKEN=os.getenv('BOOTSTRAP_TOKEN','')
DEMO_MODE=os.getenv('DEMO_MODE','false').lower()=='true'
LOGGING={'version':1,'disable_existing_loggers':False,'handlers':{'console':{'class':'logging.StreamHandler'}},'root':{'handlers':['console'],'level':'WARNING'}}

if os.getenv('TESTING')=='1':
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
