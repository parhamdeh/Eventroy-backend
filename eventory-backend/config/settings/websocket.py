from config.settings.env import env


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [env("REDIS_URL")]},
    },
}
NOTIFICATION_WS_TICKET_TTL = 30 