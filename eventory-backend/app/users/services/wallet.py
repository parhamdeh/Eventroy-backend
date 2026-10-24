from app.users.models import Wallet, User




def create_wallet(*, user: User):
    return Wallet.objects.create(
        user=user
    )