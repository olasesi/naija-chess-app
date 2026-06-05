from rest_framework import serializers
from .models import GameAnalysis, CachedPosition


class GameAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameAnalysis
        fields = [
            "gameId", "pgn", "fen", "status", "depth",
            "totalMoves", "analyzedMoves", "accuracy",
            "averageCentipawnLoss", "classifications",
            "moves", "eco", "opening", "error",
            "createdAt", "completedAt", "updatedAt",
        ]
        read_only_fields = [
            "status", "totalMoves", "analyzedMoves", "accuracy",
            "averageCentipawnLoss", "classifications", "moves",
            "eco", "opening", "error", "completedAt",
        ]


class RequestAnalysisSerializer(serializers.Serializer):
    gameId = serializers.CharField(max_length=36)
    pgn = serializers.CharField()
    fen = serializers.CharField(default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    depth = serializers.ChoiceField(choices=AnalysisDepth.choices, default="normal")


class PositionAnalysisSerializer(serializers.Serializer):
    fen = serializers.CharField()
    depth = serializers.IntegerField(default=18, min_value=4, max_value=30)
    multipv = serializers.IntegerField(default=1, min_value=1, max_value=5)


class PositionAnalysisResultSerializer(serializers.Serializer):
    fen = serializers.CharField()
    depth = serializers.IntegerField()
    score = serializers.IntegerField()
    mate = serializers.IntegerField(allow_null=True)
    bestMove = serializers.CharField()
    continuation = serializers.ListField(child=serializers.CharField())
    nodesSearched = serializers.IntegerField()
    timeMs = serializers.IntegerField()
