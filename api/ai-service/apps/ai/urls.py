from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AIAnswerView, AIGameViewSet

router = DefaultRouter()
router.register(r"ai/games", AIGameViewSet, basename="ai-game")

urlpatterns = router.urls + [
    # Stateless AI move generation: POST /api/ai/move/
    path("ai/move/", AIAnswerView.as_view({"post": "create"}), name="ai-answer"),
]