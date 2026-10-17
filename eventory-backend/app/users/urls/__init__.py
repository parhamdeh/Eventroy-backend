from django.urls import path

from app.users.apis.auth.login import (
    GoogleAuthApi,
    LoginApi,
    PasswordResetConfirmApi,
    PasswordResetRequestApi,
)
from app.users.apis.auth.refresh import TokenRefreshApi
from app.users.apis.auth.signup import SignUpApi, VerifyRegistrationApi
from app.users.apis.user.api import AdminUserDetailView, AdminUserVipView, ListCreateAdminView

urlpatterns = [
    path("auth/signup/", SignUpApi.as_view(), name="auth-signup"),
    path("auth/verify/", VerifyRegistrationApi.as_view(), name="auth-verify"),
    path("auth/login/", LoginApi.as_view(), name="auth-login"),
    path("auth/password-reset/", PasswordResetRequestApi.as_view(), name="auth-password-reset"),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmApi.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/token/refresh/", TokenRefreshApi.as_view(), name="auth-token-refresh"),
    path("auth/google/", GoogleAuthApi.as_view(), name="auth-google"),
    path("admin/users/", ListCreateAdminView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/users/<int:user_id>/vip/", AdminUserVipView.as_view(), name="admin-user-vip"),
]
