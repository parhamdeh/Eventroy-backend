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

AUTH_PASSWORD_VALIDATORS = [
    # ... existing validators
    {'NAME': 'path.to.NumberValidator'},
    {'NAME': 'path.to.LetterValidator'},
    {'NAME': 'path.to.SpecialCharValidator'},
]