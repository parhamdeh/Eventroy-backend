from django.core.management.base import BaseCommand, CommandError

from app.notification.services import create_notification, push_event


class Command(BaseCommand):
    help = (
        "Push a test event to a user's open WebSocket(s). "
        "Use it to verify the whole pipeline without touching payments."
    )

    def add_arguments(self, parser):
        parser.add_argument("--user-id", required=True)
        parser.add_argument(
            "--persist",
            action="store_true",
            help="Also store it as a real Notification (inbox) and push notification.new.",
        )
        parser.add_argument(
            "--balance",
            type=int,
            help="Push a fake wallet.balance event instead (UI testing only, DB untouched).",
        )

    def handle(self, *args, user_id, persist, balance, **options):
        if balance is not None:
            push_event(
                user_id=user_id, event="wallet.balance", payload={"balance": balance}
            )
        elif persist:
            create_notification(
                user_id=user_id, title="Test notification", body="Hello from the CLI."
            )
        else:
            push_event(user_id=user_id, event="test.ping", payload={"hello": "world"})
        self.stdout.write(self.style.SUCCESS(f"Sent to user_{user_id}."))