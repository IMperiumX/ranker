from rest_framework import serializers

from ranker.games.models import Game


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Game model."""

    class Meta:
        model = Game
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "score_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GameListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Game list views."""

    class Meta:
        model = Game
        fields = [
            "id",
            "name",
            "score_type",
            "is_active",
        ]
        read_only_fields = ["id"]
