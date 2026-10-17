"""Staff user detail by primary key. Reuses the administrator serializer."""

from app.users.apis.user.api import AdminUserDetailView

UserByIdApi = AdminUserDetailView
