from rest_framework import serializers
from .models import UserPreference


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "userId", "theme", "boardStyle", "pieceStyle",
            "soundEnabled", "showAnalysis", "autoPromote",
            "createdAt", "updatedAt",
        ]
        read_only_fields = ["userId", "createdAt", "updatedAt"]


class UserPreferenceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "theme", "boardStyle", "pieceStyle",
            "soundEnabled", "showAnalysis", "autoPromote",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}
