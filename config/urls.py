from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.views import RegisterView
from jobs.dashboard_views import (
    candidate_delete_view,
    candidate_edit_view,
    candidate_upload_view,
    home_redirect_view,
    jd_delete_view,
    jd_edit_view,
    jd_fill_view,
    result_filter_view,
)

urlpatterns = [
    path("", home_redirect_view, name="home"),
    path("jd/", jd_fill_view, name="jd-form"),
    path("jd/<int:pk>/edit/", jd_edit_view, name="jd-edit"),
    path("jd/<int:pk>/delete/", jd_delete_view, name="jd-delete"),
    path("upload-resume/", candidate_upload_view, name="candidate-upload"),
    path("candidate/<int:pk>/edit/", candidate_edit_view, name="candidate-edit"),
    path("candidate/<int:pk>/delete/", candidate_delete_view, name="candidate-delete"),
    path("result-filter/", result_filter_view, name="result-filter"),
    path("admin/", admin.site.urls),
    # Auth & JWT
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # API Schema & Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Jobs & Applications
    path("api/", include("jobs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)