import chess

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .engine import choose_move
from .models import AIGame
from .serializers import (
    AIAnswerSerializer,
    AIGameCreateSerializer,
    AIGameMoveSerializer,
    AIGameSerializer,
)
from .game_utils import apply_move, result_for_board


class AIAnswerView(viewsets.GenericViewSet):
    """
    Stateless AI move generation:
      POST /api/ai/move/
    """
    serializer_class = AIAnswerSerializer

    def create(self, request):
        serializer = AIAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            chess.Board(serializer.validated_data["fen"])
        except ValueError:
            return Response({"detail": "Invalid FEN"}, status=status.HTTP_400_BAD_REQUEST)

        result = choose_move(
            serializer.validated_data["fen"],
            serializer.validated_data.get("level", "medium"),
        )
        return Response(result)


class AIGameViewSet(viewsets.ModelViewSet):
    """Persistent games against the AI."""

    queryset = AIGame.objects.all()
    serializer_class = AIGameSerializer

    def get_queryset(self):
        return self.queryset.filter(user_id=self.request.user.id)

    def create(self, request):
        serializer = AIGameCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fen = serializer.validated_data.get("fen") or None
        if fen:
            try:
                chess.Board(fen)
            except ValueError:
                return Response({"detail": "Invalid FEN"}, status=status.HTTP_400_BAD_REQUEST)

        game = AIGame.objects.create(
            user_id=request.user.id,
            side=serializer.validated_data["side"],
            level=serializer.validated_data["level"],
            fen=fen or AIGame._meta.get_field("fen").default,
        )

        # If the player chose black, the AI moves first from the opening position.
        data = AIGameSerializer(game).data
        if game.side == "b":
            reply = choose_move(game.fen, game.level)
            if reply["move"]:
                apply_move(game, reply["move"])
                game.refresh_from_db()
                data = AIGameSerializer(game).data
                data["ai_move"] = reply["move"]
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def move(self, request, pk=None):
        """Player move + automatic AI reply."""
        game = self.get_object()
        serializer = AIGameMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if game.result != AIGame.Result.PENDING:
            return Response({"detail": "Game already finished"}, status=status.HTTP_400_BAD_REQUEST)

        board = chess.Board(game.fen)

        try:
            move = board.parse_uci(
                serializer.validated_data["from_square"] + serializer.validated_data["to_square"]
                + (serializer.validated_data.get("promotion") or "")
            )
        except ValueError:
            return Response({"detail": "Illegal move"}, status=status.HTTP_400_BAD_REQUEST)

        if move not in board.legal_moves:
            return Response({"detail": "Illegal move"}, status=status.HTTP_400_BAD_REQUEST)

        san = board.san(move)
        board.push(move)
        game.fen = board.fen()
        game.moves = game.moves + [san]
        game.result = result_for_board(board)
        if board.is_game_over():
            game.draw_reason = board.outcome().termination.name if board.outcome() else ""
        game.save()

        ai_reply = None
        if game.result == AIGame.Result.PENDING and not board.is_game_over():
            reply = choose_move(game.fen, game.level)
            if reply["move"]:
                apply_move(game, reply["move"])
                ai_reply = reply["move"]
                game.refresh_from_db()

        data = AIGameSerializer(game).data
        data["ai_move"] = ai_reply
        return Response(data)

    @action(detail=False, methods=["GET"])
    def history(self, request):
        """The current user's past AI games."""
        games = self.get_queryset()[:50]
        return Response(AIGameSerializer(games, many=True).data)