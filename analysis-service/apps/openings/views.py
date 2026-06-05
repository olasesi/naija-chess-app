from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Opening
from .serializers import OpeningSerializer
from .utils import detect_opening_from_fen, detect_opening_from_moves


class OpeningDetailView(APIView):
    permission_classes = []  # Public

    def get(self, request, eco):
        try:
            opening = Opening.objects.get(eco=eco.upper())
            serializer = OpeningSerializer(opening)
            return Response(serializer.data)
        except Opening.DoesNotExist:
            return Response(
                {"success": False, "message": "Opening not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class OpeningSearchView(APIView):
    permission_classes = []  # Public

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {"success": False, "message": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        openings = Opening.objects.filter(name__icontains=query)[:20]
        serializer = OpeningSerializer(openings, many=True)
        return Response(serializer.data)


class OpeningFromFenView(APIView):
    permission_classes = []  # Public

    def get(self, request):
        fen = request.query_params.get("fen", "")
        if not fen:
            return Response(
                {"success": False, "message": "FEN is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        eco, name = detect_opening_from_fen(fen)
        return Response({"eco": eco, "name": name})


class OpeningFromMovesView(APIView):
    permission_classes = []  # Public

    def post(self, request):
        moves = request.data.get("moves", [])
        if not moves:
            return Response(
                {"success": False, "message": "Moves required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        eco, name = detect_opening_from_moves(moves)
        return Response({"eco": eco, "name": name, "moves": moves})
