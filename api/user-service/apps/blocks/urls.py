from django.urls import path

from .views import BlockListView, BlockRemoveView, BlockStatusView

urlpatterns = [
    path("blocks", BlockListView.as_view(), name="blocks-list"),
    path("blocks/status/<str:targetId>", BlockStatusView.as_view(), name="blocks-status"),
    path("blocks/<str:targetId>", BlockRemoveView.as_view(), name="blocks-remove"),
]