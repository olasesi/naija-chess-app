from django.urls import path
from .views import PreferenceDetailView

urlpatterns = [
    path("preferences", PreferenceDetailView.as_view(), name="preferences-detail"),
]
