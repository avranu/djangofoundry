from __future__ import annotations

# Django imports
from django.urls import include, path, re_path

# 3rd Party imports
from rest_framework import routers

# App Imports
from dashboard.controllers import home

app_name = "dashboard"

# Define all our REST API routes
routes = {
    #"people": PersonViewSet,
    #'celery': TaskStatusViewSet,
}

# Use the default router to define endpoints
router = routers.DefaultRouter()
# Register each viewset with the router
for route, viewset in routes.items():
    if hasattr(viewset, "basename"):
        router.register(route, viewset, basename = getattr(viewset, "basename"))
    else:
        router.register(route, viewset)

urlpatterns = [
    # /dashboard/rest/
    re_path(r"rest/?", include(router.urls)),

    # /dashboard/
    path("", home.IndexController.as_view(), name="index"),
]
