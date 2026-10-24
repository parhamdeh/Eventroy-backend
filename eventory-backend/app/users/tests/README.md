# User/authentication tests

These tests were drafted against the application code included with the project archive. They were **not executed**.

## Run

From the repository root, with the project's test dependencies installed:

```bash
pytest --ds=config.django.test app/users/tests/test_otp_unit.py
pytest --ds=config.django.test app/users/tests/test_auth_services.py
pytest --ds=config.django.test app/users/tests/test_auth_api.py
pytest --ds=config.django.test app/users/tests --cov=app.users --cov-report=term-missing
```

The test settings use an in-memory SQLite database and local-memory cache, and Celery message dispatch is mocked in HTTP tests. No real SMS or email should be sent.

## Coverage groups

- `test_otp_unit.py`: OTP generation, storage/digest, cooldown, successful consumption, wrong attempts, expiration, purpose isolation, and cache failure mapping.
- `test_auth_services.py`: login service behavior and password-reset service behavior.
- `test_auth_api.py`: HTTP-level signup/verification, login, password reset, one-time OTP behavior, and an unauthenticated admin request.

One signup regression assertion checks that the password chosen at signup remains usable after OTP verification. The current source appears to hash the password before passing it to a manager that hashes passwords again; if that assertion fails, investigate the signup password-hashing flow rather than weakening the test.
