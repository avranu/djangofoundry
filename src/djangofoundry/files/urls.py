from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView

# Django imports
from django.urls import include, re_path
from django.views.generic import RedirectView

# 3rd Party imports
# from two_factor.urls import urlpatterns as tf_urls

# NOTE: may not be needed here.
admin.autodiscover()

urlpatterns = [
    # path('', include(tf_urls)),
    re_path("admin/", admin.site.urls),
    re_path("dashboard/", include("dashboard.urls")),
    re_path("__debug__/", include("debug_toolbar.urls")),
    re_path("api-auth/", include("rest_framework.urls")),
    re_path(r"login/?", LoginView.as_view(), name="login"),
    re_path(r"logout/?", LogoutView.as_view(), name="logout"),
    re_path(r"^/?$", RedirectView.as_view(url='/dashboard/', permanent=False), name='redirect_dashboard'),
]
