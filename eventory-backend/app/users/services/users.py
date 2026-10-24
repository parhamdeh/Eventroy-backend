from app.users.models import User
from app.users.services.wallet import create_wallet
from app.utils.types.django.models import DjangoModelType

from django.db import transaction


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