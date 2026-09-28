from rest_framework import serializers
from .models import Opening


class OpeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opening
        fields = ["eco", "name", "moves", "popularity"]


class OpeningSearchSerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2)


class FenOpeningSerializer(serializers.Serializer):
    fen = serializers.CharField()
