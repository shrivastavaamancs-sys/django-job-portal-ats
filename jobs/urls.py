from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet,
    ApplyJobView,
    MyApplicationsListView,
    UpdateApplicationStatusView,
)

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="jobs")

urlpatterns = [
    path("", include(router.urls)),
    path("applications/apply/", ApplyJobView.as_view(), name="apply-job"),
    path("applications/", MyApplicationsListView.as_view(), name="my-applications"),
    path("applications/<int:pk>/status/", UpdateApplicationStatusView.as_view(), name="update-status"),
]