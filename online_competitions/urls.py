

import allauth.account.views as allauth_views
from django.contrib import admin
from django.urls import include, path, re_path

from kos.views import LoginFormView, SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Allauth
    re_path(r'^accounts/confirm-email/(?P<key>[-:\w]+)/$',
            allauth_views.confirm_email, name='account_confirm_email'),
    path("password/reset/", allauth_views.password_reset,
         name="account_reset_password"),
    path(
        "password/reset/done/",
        allauth_views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        allauth_views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        allauth_views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
    path('login', LoginFormView.as_view(), name='account_login'),
    path('register', SignUpView.as_view(), name='account_signup'),
    path('', include('kos.urls', namespace='kos'))
]
handler404 = 'kos.views.view_404'
