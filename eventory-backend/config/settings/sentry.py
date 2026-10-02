from config.env import env

SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    environment = env("SENTRY_ENVIRONMENT", default="local")
    track_performance = environment == "production"

    import sentry_sdk

    def traces_sampler(sampling_context):
        if not track_performance:
            return 0

        transaction_context = sampling_context.get("transaction_context")
        if transaction_context is None:
            return 0

        op = transaction_context.get("op")
        if op is None:
            return 0

        if op == "celery.task":
            return 0

        return 0.5

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=environment,
        traces_sampler=traces_sampler,
        send_default_pii=False,
    )