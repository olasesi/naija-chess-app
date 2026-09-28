from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SignalViewSet, FlagViewSet, SanctionViewSet, UserRadarView

router = DefaultRouter()
router.register(r"signals", SignalViewSet, basename="signal")
router.register(r"flags", FlagViewSet, basename="flag")
router.register(r"sanctions", SanctionViewSet, basename="sanction")

urlpatterns = [
    path("anticheat/", include(router.urls)),
    path("anticheat/users/<str:user_id>/", UserRadarView.as_view()),
]