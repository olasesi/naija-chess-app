from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BlockType, UserBlock
from .serializers import UserBlockCreateSerializer, UserBlockSerializer


class BlockListView(APIView):
    def get(self, request):
        userId = getattr(request.user, "id", None)
        block_type = request.query_params.get("type")

        queryset = UserBlock.objects.filter(userId=userId)
        if block_type:
            queryset = queryset.filter(type=block_type)

        queryset = queryset.order_by("-createdAt")
        serializer = UserBlockSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        userId = getattr(request.user, "id", None)
        serializer = UserBlockCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        blockedId = str(serializer.validated_data["blockedId"])
        block_type = serializer.validated_data["type"]
        reason = serializer.validated_data.get("reason", "")

        if userId == blockedId:
            return Response(
                {"success": False, "message": "Cannot block or mute yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = UserBlock.objects.filter(
            userId=userId,
            blockedId=blockedId,
            type=block_type,
        ).first()
        if existing:
            return Response(
                {"success": False, "message": f"User already {'blocked' if block_type == BlockType.BLOCK else 'muted'}"},
                status=status.HTTP_409_CONFLICT,
            )

        relationship = UserBlock.objects.create(
            userId=userId,
            blockedId=blockedId,
            type=block_type,
            reason=reason,
        )
        return Response(
            UserBlockSerializer(relationship).data,
            status=status.HTTP_201_CREATED,
        )


class BlockStatusView(APIView):
    def get(self, request, targetId):
        userId = getattr(request.user, "id", None)

        blocking = UserBlock.objects.filter(
            userId=userId, blockedId=targetId, type=BlockType.BLOCK
        ).exists()
        muting = UserBlock.objects.filter(
            userId=userId, blockedId=targetId, type=BlockType.MUTE
        ).exists()
        blockedBy = UserBlock.objects.filter(
            userId=targetId, blockedId=userId, type=BlockType.BLOCK
        ).exists()
        mutedBy = UserBlock.objects.filter(
            userId=targetId, blockedId=userId, type=BlockType.MUTE
        ).exists()

        return Response(
            {
                "targetId": targetId,
                "blocking": blocking,
                "muting": muting,
                "blockedBy": blockedBy,
                "mutedBy": mutedBy,
                "isBlocked": blockedBy,
                "isMuted": mutedBy,
            }
        )


class BlockRemoveView(APIView):
    def delete(self, request, targetId):
        userId = getattr(request.user, "id", None)
        UserBlock.objects.filter(
            userId=userId,
            blockedId=targetId,
        ).delete()
        return Response(
            {"success": True, "message": "Relationship removed"},
            status=status.HTTP_200_OK,
        )