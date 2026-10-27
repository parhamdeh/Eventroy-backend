# Adjust the import path to wherever your ApplicationError lives.
from app.core.exceptions import ApplicationError


class WalletError(ApplicationError):
    """Base class for wallet errors."""


class InsufficientBalance(WalletError):
    """The wallet does not hold enough balance for the requested debit."""


class InvalidAmount(WalletError):
    """Amount must be a positive integer (Iranian tomans)."""