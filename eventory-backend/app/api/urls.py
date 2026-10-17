from django.urls import include, path

urlpatterns = [
    path("", include(("app.users.urls", "users"))),
]
