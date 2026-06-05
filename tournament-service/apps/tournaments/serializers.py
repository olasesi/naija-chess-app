from rest_framework import serializers
from .models import Tournament, TournamentPlayer, TournamentRound, TournamentMatch


class TournamentSerializer(serializers.ModelSerializer):
    player_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    creator_username = serializers.CharField(read_only=True, default="")

    class Meta:
        model = Tournament
        fields = [
            "id", "name", "description", "type", "status",
            "time_control_initial", "time_control_increment",
            "rating_min", "rating_max", "max_players", "min_players",
            "total_rounds", "current_round", "creator_id", "creator_username",
            "allow_bye", "start_date", "end_date",
            "player_count", "is_full",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "current_round", "start_date", "end_date", "created_at", "updated_at"]

    def get_player_count(self, obj):
        return obj.players.count()

    def get_is_full(self, obj):
        return obj.players.count() >= obj.max_players


class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = [
            "name", "description", "type",
            "time_control_initial", "time_control_increment",
            "rating_min", "rating_max", "max_players", "min_players",
            "total_rounds", "allow_bye",
        ]

    def validate_max_players(self, value):
        if value < 2:
            raise serializers.ValidationError("max_players must be at least 2")
        return value

    def validate_total_rounds(self, value):
        if value < 1:
            raise serializers.ValidationError("total_rounds must be at least 1")
        return value

    def validate(self, data):
        if data.get("rating_min") and data.get("rating_max"):
            if data["rating_min"] > data["rating_max"]:
                raise serializers.ValidationError("rating_min must be <= rating_max")
        return data


class TournamentPlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True, default="")

    class Meta:
        model = TournamentPlayer
        fields = [
            "id", "user_id", "username", "seed", "score",
            "tiebreak1", "tiebreak2", "has_bye", "is_active", "joined_at",
        ]
        read_only_fields = ["id", "seed", "score", "tiebreak1", "tiebreak2", "has_bye", "joined_at"]


class TournamentRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentRound
        fields = ["id", "round_number", "status", "started_at", "completed_at"]
        read_only_fields = ["id"]


class TournamentMatchSerializer(serializers.ModelSerializer):
    white_user_id = serializers.CharField(source="white_player.user_id", read_only=True, default="")
    black_user_id = serializers.CharField(source="black_player.user_id", read_only=True, default="")
    round_number = serializers.IntegerField(source="round.round_number", read_only=True)

    class Meta:
        model = TournamentMatch
        fields = [
            "id", "tournament_id", "round_id", "round_number",
            "white_user_id", "black_user_id",
            "game_id", "result", "status", "board_number",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "game_id", "status"]


class TournamentStandingSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.CharField()
    username = serializers.CharField(default="")
    score = serializers.FloatField()
    tiebreak1 = serializers.FloatField()
    tiebreak2 = serializers.FloatField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    draws = serializers.IntegerField()
    byes = serializers.IntegerField()
