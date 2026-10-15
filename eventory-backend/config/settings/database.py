# import os



# DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.environ["POSTGRES_DB"],
#             'USER': os.environ["POSTGRES_USER"],
#             'PASSWORD': os.environ["POSTGRES_PASSWORD"],
#             'HOST': os.environ["POSTGRES_HOST"],
#             'PORT': os.environ["POSTGRES_PORT"],
#         }
#     }


from config.settings.env import env

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    },
}