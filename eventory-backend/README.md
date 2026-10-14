# Eventory backend

Django + DRF event-ticketing backend (PostgreSQL, Redis, Celery/RabbitMQ, Elasticsearch).

## Local setup

1. Create a virtualenv (Python 3.14, see `runtime.txt`; Django 6 needs 3.12+)

   ```bash
   python3.14 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies (`requirements_dev.txt` already includes `requirements.txt`)

   ```bash
   pip install -r requirements_dev.txt
   ```

3. Create your environment file and replace every `change-me` placeholder

   ```bash
   cp .env.example .env
   ```

4. Start the infrastructure (database must be up **before** migrating)

   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

5. Create tables

   ```bash
   python manage.py migrate
   ```

6. Run the project

   ```bash
   python manage.py runserver
   ```

7. Run a Celery worker

   ```bash
   celery -A config worker -l info --pool=solo
   ```

## Settings modules

| Purpose     | Module                       |
|-------------|------------------------------|
| Local dev   | `config.django.local`        |
| Tests       | `config.django.test`         |
| Production  | `config.django.production`   |

## Quality checks

```bash
ruff check .
mypy .
pytest --cov
```