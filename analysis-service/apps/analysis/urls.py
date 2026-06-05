from django.urls import path
from .views import (
    RequestGameAnalysisView,
    GetGameAnalysisView,
    GetGameAnalysisStatusView,
    AnalyzePositionView,
    GetBestMoveView,
)

urlpatterns = [
    path("games/analyze", RequestGameAnalysisView.as_view(), name="analysis-request"),
    path("games/<str:gameId>", GetGameAnalysisView.as_view(), name="analysis-detail"),
    path("games/<str:gameId>/status", GetGameAnalysisStatusView.as_view(), name="analysis-status"),
    path("position", AnalyzePositionView.as_view(), name="analysis-position"),
    path("best-move", GetBestMoveView.as_view(), name="analysis-best-move"),
]
