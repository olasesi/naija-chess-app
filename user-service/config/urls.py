from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API
    path("api/users/", include("apps.profiles.urls")),
    path("api/users/", include("apps.stats.urls")),
    path("api/users/", include("apps.friends.urls")),
    path("api/users/", include("apps.preferences.urls")),
    # Health
    path("health/", include("health_check.urls")),
    # Documentation
    path("api/docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
