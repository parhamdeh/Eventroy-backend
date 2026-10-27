import pytest
from django.core.management import call_command

from app.users.models import Wallet
from app.users.services import credit_wallet, debit_wallet

pytestmark = pytest.mark.django_db


def _wallet_with_history(user):
    credit_wallet(user_id=user.pk, amount=10_000, idempotency_key="t:1")
    debit_wallet(user_id=user.pk, amount=2_500, idempotency_key="t:2")
    return Wallet.objects.get(user=user)  # ledger says 7_500


def test_dry_run_reports_but_does_not_write(user):
    wallet = _wallet_with_history(user)
    Wallet.objects.filter(pk=wallet.pk).update(balance=1)

    call_command("recalculate_wallet_balances")

    assert Wallet.objects.get(pk=wallet.pk).balance == 1


def test_fix_restores_balance_from_ledger(user):
    wallet = _wallet_with_history(user)
    Wallet.objects.filter(pk=wallet.pk).update(balance=999_999)

    call_command("recalculate_wallet_balances", "--fix")

    assert Wallet.objects.get(pk=wallet.pk).balance == 7_500


def test_wallet_without_ledger_is_skipped_unless_forced(user):
    wallet = Wallet.objects.create(user=user, balance=500)

    call_command("recalculate_wallet_balances", "--fix")
    assert Wallet.objects.get(pk=wallet.pk).balance == 500

    call_command("recalculate_wallet_balances", "--fix", "--include-empty")
    assert Wallet.objects.get(pk=wallet.pk).balance == 0