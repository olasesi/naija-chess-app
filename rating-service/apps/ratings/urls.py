from django.urls import path
from .views import RatingDetailView, RatingHistoryView, UpdateRatingView

urlpatterns = [
    path("me", RatingDetailView.as_view(), name="rating-me"),
    path("me/history", RatingHistoryView.as_view(), name="rating-history-me"),
    path("<str:userId>", RatingDetailView.as_view(), name="rating-detail"),
    path("<str:userId>/history", RatingHistoryView.as_view(), name="rating-history"),
    path("update", UpdateRatingView.as_view(), name="rating-update"),
]
