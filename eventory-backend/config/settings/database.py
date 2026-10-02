import os
from config.env import env, BASE_DIR

env.read_env(os.path.join(BASE_DIR, ".env"))

DATABASES = {
    'default': env.db('DATABASE_URL', default='psql://parham:paripari85@127.0.0.1:5432/eventory-backend'),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

if os.environ.get('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'github_actions',
            'USER': 'parham',
            'PASSWORD': 'paripari85',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }