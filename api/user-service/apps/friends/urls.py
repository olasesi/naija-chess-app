from django.urls import path
from .views import FriendListView, FriendRequestView, FriendActionView, FriendRemoveView

urlpatterns = [
    path("friends", FriendListView.as_view(), name="friends-list"),
    path("friends/request", FriendRequestView.as_view(), name="friends-request"),
    path("friends/request/<str:friendId>", FriendActionView.as_view(), name="friends-action"),
    path("friends/<str:friendId>", FriendRemoveView.as_view(), name="friends-remove"),
]
