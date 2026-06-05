from django.urls import path
from .views import OpeningDetailView, OpeningSearchView, OpeningFromFenView, OpeningFromMovesView

urlpatterns = [
    path("openings/search", OpeningSearchView.as_view(), name="openings-search"),
    path("openings/from-fen", OpeningFromFenView.as_view(), name="openings-from-fen"),
    path("openings/from-moves", OpeningFromMovesView.as_view(), name="openings-from-moves"),
    path("openings/<str:eco>", OpeningDetailView.as_view(), name="openings-detail"),
]
