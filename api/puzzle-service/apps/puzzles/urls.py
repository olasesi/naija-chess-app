from rest_framework.routers import DefaultRouter
from .views import PuzzleViewSet

router = DefaultRouter()
router.register(r"puzzles", PuzzleViewSet, basename="puzzle")

urlpatterns = router.urls
