from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Friend, FriendStatus
from .serializers import (
    FriendSerializer,
    FriendRequestSerializer,
    FriendActionSerializer,
)


class FriendListView(APIView):
    def get(self, request):
        userId = getattr(request.user, "id", None)
        status_filter = request.query_params.get("status", FriendStatus.ACCEPTED)

        friendships = Friend.objects.filter(
            Q(userId=userId) | Q(friendId=userId),
            status=status_filter,
        ).order_by("-createdAt")

        serializer = FriendSerializer(friendships, many=True)

        # Normalize so friendId always points to the other user
        data = []
        for item in serializer.data:
            if item["userId"] == userId:
                data.append(item)
            else:
                item["friendId"] = item["userId"]
                item["userId"] = userId
                data.append(item)

        return Response(data)


class FriendRequestView(APIView):
    def post(self, request):
        userId = getattr(request.user, "id", None)
        serializer = FriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        friendId = str(serializer.validated_data["friendId"])

        if userId == friendId:
            return Response(
                {"success": False, "message": "Cannot friend yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check existing relationship
        existing = Friend.objects.filter(
            Q(userId=userId, friendId=friendId)
            | Q(userId=friendId, friendId=userId)
        ).first()

        if existing:
            messages = {
                FriendStatus.ACCEPTED: "Already friends",
                FriendStatus.PENDING: "Request already exists",
                FriendStatus.BLOCKED: "Relationship blocked",
            }
            return Response(
                {"success": False, "message": messages.get(existing.status, "Conflict")},
                status=status.HTTP_409_CONFLICT,
            )

        friend = Friend.objects.create(userId=userId, friendId=friendId)
        return Response(
            FriendSerializer(friend).data,
            status=status.HTTP_201_CREATED,
        )


class FriendActionView(APIView):
    def patch(self, request, friendId):
        userId = getattr(request.user, "id", None)
        serializer = FriendActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        try:
            friendship = Friend.objects.get(
                userId=friendId,
                friendId=userId,
                status=FriendStatus.PENDING,
            )
        except Friend.DoesNotExist:
            return Response(
                {"success": False, "message": "Friend request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == "accept":
            friendship.status = FriendStatus.ACCEPTED
            friendship.save()
        elif action == "decline":
            friendship.delete()
            return Response(
                FriendSerializer(friendship).data,
            )
        elif action == "block":
            friendship.delete()
            blocked = Friend.objects.create(
                userId=userId,
                friendId=friendId,
                status=FriendStatus.BLOCKED,
            )
            return Response(FriendSerializer(blocked).data)

        return Response(FriendSerializer(friendship).data)


class FriendRemoveView(APIView):
    def delete(self, request, friendId):
        userId = getattr(request.user, "id", None)
        Friend.objects.filter(
            Q(userId=userId, friendId=friendId)
            | Q(userId=friendId, friendId=userId)
        ).delete()
        return Response(
            {"success": True, "message": "Friend removed"},
            status=status.HTTP_200_OK,
        )
