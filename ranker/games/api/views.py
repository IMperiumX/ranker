from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ranker.games.models import Game

from .serializers import GameListSerializer
from .serializers import GameSerializer


class GameViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet for Game model.

    Provides list and retrieve operations for games.
    Only active games are shown to regular users.
    """

    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return queryset based on user permissions."""
        queryset = Game.objects.all()

        # Only show active games to regular users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("name")

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "list":
            return GameListSerializer
        return GameSerializer

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get all active games."""
        active_games = Game.objects.filter(is_active=True).order_by("name")
        serializer = GameListSerializer(active_games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
