from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner
from .models import UserPreference
from .serializers import (
    UserPreferenceSerializer,
    UserPreferenceUpdateSerializer,
)


class PreferenceDetailView(APIView):
    permission_classes = [IsOwner]

    def get_object(self, userId):
        pref, created = UserPreference.objects.get_or_create(userId=userId)
        return pref

    def get(self, request):
        userId = getattr(request.user, "id", None)
        pref = self.get_object(userId)
        serializer = UserPreferenceSerializer(pref)
        return Response(serializer.data)

    def patch(self, request):
        userId = getattr(request.user, "id", None)
        pref = self.get_object(userId)
        self.check_object_permissions(request, pref)

        serializer = UserPreferenceUpdateSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserPreferenceSerializer(pref).data)
