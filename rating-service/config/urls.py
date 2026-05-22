from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/ratings/", include("apps.ratings.urls")),
    path("api/ratings/", include("apps.leaderboards.urls")),
    path("health/", include("health_check.urls")),
    path("api/docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
