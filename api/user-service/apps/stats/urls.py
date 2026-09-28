from django.urls import path
from .views import StatsDetailView, RecordGameResultView

urlpatterns = [
    path("stats/me", StatsDetailView.as_view(), name="stats-me"),
    path("stats/record", RecordGameResultView.as_view(), name="stats-record"),
    path("stats/<str:userId>", StatsDetailView.as_view(), name="stats-detail"),
]
