from rest_framework import serializers

from .models import AIGame


class AIGameSerializer(serializers.ModelSerializer):
    pgn = serializers.CharField(read_only=True)

    class Meta:
        model = AIGame
        fields = [
            "id",
            "user_id",
            "side",
            "level",
            "fen",
            "moves",
            "result",
            "draw_reason",
            "pgn",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "fen", "moves", "result", "draw_reason", "created_at", "updated_at"]


class AIGameCreateSerializer(serializers.Serializer):
    side = serializers.ChoiceField(choices=["w", "b"], default="w")
    level = serializers.ChoiceField(
        choices=["beginner", "easy", "medium", "hard", "expert"], default="medium"
    )
    fen = serializers.CharField(required=False, allow_blank=True)


class AIAnswerSerializer(serializers.Serializer):
    fen = serializers.CharField()
    level = serializers.ChoiceField(
        choices=["beginner", "easy", "medium", "hard", "expert"], default="medium"
    )


class AIGameMoveSerializer(serializers.Serializer):
    from_square = serializers.CharField(max_length=2)
    to_square = serializers.CharField(max_length=2)
    promotion = serializers.CharField(required=False, allow_null=True)