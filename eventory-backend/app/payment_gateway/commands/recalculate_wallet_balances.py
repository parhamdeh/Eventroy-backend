from functools import partial

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.users.models import Wallet, WalletTransaction
from app.payment_gateway.notification import notify_balance_changed
from app.users.services import calculate_ledger_balance

Direction = WalletTransaction.Direction


class Command(BaseCommand):
    help = (
        "Recompute every wallet balance from its ledger (WalletTransaction) and "
        "report / repair wallets whose stored balance disagrees. "
        "DRY-RUN by default: nothing is written unless you pass --fix."
    )

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Write the corrected balances.")
        parser.add_argument("--user-id", help="Only check this user's wallet.")
        parser.add_argument(
            "--include-empty",
            action="store_true",
            help=(
                "Also reset wallets that have a balance but NO ledger rows to 0. "
                "Off by default because such wallets usually hold legacy money "
                "that was never recorded in the ledger."
            ),
        )
        parser.add_argument(
            "--verify-chain",
            action="store_true",
            help="Also check that every entry's balance_after matches the running total.",
        )

    def handle(self, *args, fix, user_id, include_empty, verify_chain, **options):
        wallets = Wallet.objects.order_by("pk")
        if user_id:
            wallets = wallets.filter(user_id=user_id)

        stats = {"checked": 0, "ok": 0, "mismatch": 0, "fixed": 0, "skipped": 0, "negative": 0, "chain": 0}

        for wallet_id in wallets.values_list("pk", flat=True).iterator(chunk_size=500):
            stats["checked"] += 1
            self._process(wallet_id, fix, include_empty, verify_chain, stats)

        self.stdout.write("")
        self.stdout.write(
            f"checked={stats['checked']} ok={stats['ok']} mismatch={stats['mismatch']} "
            f"fixed={stats['fixed']} skipped={stats['skipped']} "
            f"negative={stats['negative']} broken_chain={stats['chain']}"
        )
        if stats["mismatch"] and not fix:
            self.stdout.write(self.style.WARNING("Dry-run only. Re-run with --fix to apply."))
        if stats["negative"]:
            raise CommandError(
                f"{stats['negative']} wallet(s) have debits larger than credits; "
                "that needs manual investigation, nothing was changed for them."
            )

    # ------------------------------------------------------------------
    def _process(self, wallet_id, fix, include_empty, verify_chain, stats):
        with transaction.atomic():
            qs = Wallet.objects.all()
            if fix:
                # Lock BEFORE computing so a concurrent credit/debit can't
                # slip in between the calculation and the write.
                qs = qs.select_for_update()
            try:
                wallet = qs.get(pk=wallet_id)
            except Wallet.DoesNotExist:
                return

            expected = calculate_ledger_balance(wallet_id=wallet.pk)
            has_entries = WalletTransaction.objects.filter(wallet_id=wallet.pk).exists()
            label = f"wallet={wallet.pk} user={wallet.user_id}"

            if verify_chain:
                broken = self._first_broken_entry(wallet.pk)
                if broken is not None:
                    stats["chain"] += 1
                    self.stdout.write(self.style.ERROR(f"{label}: ledger chain broken at entry {broken}"))

            if expected < 0:
                stats["negative"] += 1
                self.stdout.write(self.style.ERROR(f"{label}: ledger total is negative ({expected})"))
                return

            if expected == wallet.balance:
                stats["ok"] += 1
                return

            stats["mismatch"] += 1
            self.stdout.write(
                f"{label}: stored={wallet.balance} ledger={expected} diff={expected - wallet.balance:+d}"
            )

            if not has_entries and not include_empty:
                stats["skipped"] += 1
                self.stdout.write(self.style.WARNING(f"{label}: no ledger rows, skipped (use --include-empty)"))
                return

            if fix:
                wallet.balance = expected
                wallet.save()  # row is locked; plain save also bumps updated_at
                transaction.on_commit(
                    partial(notify_balance_changed, user_id=wallet.user_id, balance=expected)
                )
                stats["fixed"] += 1
                self.stdout.write(self.style.SUCCESS(f"{label}: fixed -> {expected}"))

    @staticmethod
    def _first_broken_entry(wallet_id):
        running = 0
        entries = (
            WalletTransaction.objects.filter(wallet_id=wallet_id)
            .order_by("created_at", "pk")
            .values_list("pk", "direction", "amount", "balance_after")
            .iterator()
        )
        for pk, direction, amount, balance_after in entries:
            running += amount if direction == Direction.CREDIT else -amount
            if running != balance_after:
                return pk
        return None