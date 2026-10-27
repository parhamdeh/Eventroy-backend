import logging

from app.notification.services import push_event

logger = logging.getLogger(__name__)


def notify_balance_changed(*, user_id, balance: int) -> None:
    """
    Push the new balance to every open client of the user.

    Called via transaction.on_commit, so clients never see a balance that
    was later rolled back. It must never break money movement.
    """
    try:
        push_event(
            user_id=user_id,
            event="wallet.balance",
            payload={"balance": balance},
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to push wallet balance for user %s", user_id)