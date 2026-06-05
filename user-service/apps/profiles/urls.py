from django.urls import path
from .views import ProfileDetailView, ProfileSearchView, AvatarUploadView

urlpatterns = [
    path("profiles/me", ProfileDetailView.as_view(), name="profile-me"),
    path("profiles/search", ProfileSearchView.as_view(), name="profile-search"),
    path("profiles/me/avatar", AvatarUploadView.as_view(), name="profile-avatar"),
    path("profiles/<str:userId>", ProfileDetailView.as_view(), name="profile-detail"),
]
