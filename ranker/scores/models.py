from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ranker.games.models import Game

User = get_user_model()


class Score(models.Model):
    """
    Model to store user scores for different games.
    This provides persistent storage and history tracking.
    Real-time leaderboard queries are handled by Redis.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name=_("User"),
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name=_("Game"),
    )

    score = models.DecimalField(
        _("Score"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_("The score value submitted by the user"),
    )

    submitted_at = models.DateTimeField(
        _("Submitted At"),
        auto_now_add=True,
        help_text=_("When the score was submitted"),
    )

    # Optional metadata
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional game-specific data (e.g., level, time taken)"),
    )

    class Meta:
        verbose_name = _("Score")
        verbose_name_plural = _("Scores")
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["user", "game"]),
            models.Index(fields=["game", "-score"]),
            models.Index(fields=["game", "-submitted_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.game.name}: {self.score}"

    def save(self, *args, **kwargs):
        """Override save to update Redis leaderboard after saving to database."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update Redis leaderboard after saving
        if is_new:
            self.update_redis_leaderboard()

    def update_redis_leaderboard(self):
        """Update Redis leaderboard with this score."""
        from .services import LeaderboardService

        service = LeaderboardService()
        service.update_user_score(
            game_id=self.game.id,
            user_id=self.user.id,
            score=float(self.score),
            game_score_type=self.game.score_type,
        )

    @classmethod
    def get_user_best_score(cls, user, game):
        """Get the user's best score for a specific game."""
        scores = cls.objects.filter(user=user, game=game)

        if game.score_type == "highest":
            return scores.order_by("-score").first()
        # lowest or time
        return scores.order_by("score").first()

    @classmethod
    def get_user_score_history(cls, user, game, limit=None):
        """Get the user's score history for a specific game."""
        queryset = cls.objects.filter(user=user, game=game).order_by("-submitted_at")

        if limit:
            queryset = queryset[:limit]

        return queryset
