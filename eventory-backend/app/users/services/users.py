from app.users.models import User
from app.users.services.wallet import create_wallet
from app.utils.types.django.models import DjangoModelType
from app.core.exceptions import NotFoundError
from app.users.selectors.users import user_get_by_id

from django.db import transaction
from django.utils.translation import gettext as _



@transaction.atomic
def create_user(*, data: dict) -> DjangoModelType[User]:
    
    user = User.objects.create_user(
        phone= data["phone"],
        username= data["username"],
        last_name= data["last_name"],
        email= data["email"],
        birth_date= data["birth_date"],
        is_active=True,
        is_staff=False,
        is_superuser=False,
        is_vip=False,
        is_phone_verified=data["is_phone_verified"],
        is_email_verified=data["is_email_verified"],
        password = data["password"]
    )

    wallet = create_wallet(
        user=user
    )
    return user

def create_superuser(*, data: dict) -> DjangoModelType[User]:
    """
        Create a staff administrator.
    
        Superuser privileges are never granted here. VIP is always false.
        """
    return User.objects.create_superuser(
        phone= data["phone"],
        username= data["username"],
        last_name= data["last_name"],
        password = data["password"]

    )

def set_user_vip(*, user_id: int, is_vip: bool) -> User:
    """Set VIP status for an existing user."""

    user = user_get_by_id(user_id=user_id)
    if user is None:
        raise NotFoundError(_("User not found."))

    if user.is_vip == is_vip:
        return user

    with transaction.atomic():
        user.is_vip = is_vip
        user.save(update_fields=["is_vip", "updated_at"])
    return user
