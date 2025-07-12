from django.db import models
from django.utils.translation import gettext_lazy as _


class Game(models.Model):
    """
    Model to represent different games or activities that users can submit scores for.
    Each game has its own leaderboard.
    """

    name = models.CharField(
        _("Game Name"),
        max_length=100,
        unique=True,
        help_text=_("Name of the game or activity"),
    )

    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of the game rules or activity"),
    )

    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this game is currently accepting score submissions"),
    )

    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    # Scoring configuration
    score_type = models.CharField(
        _("Score Type"),
        max_length=20,
        choices=[
            ("highest", _("Highest Score Wins")),
            ("lowest", _("Lowest Score Wins")),
            ("time", _("Best Time Wins")),
        ],
        default="highest",
        help_text=_("How scores should be ranked"),
    )

    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def redis_key(self):
        """
        Redis key for this game's leaderboard sorted set.
        """
        return f"leaderboard:{self.id}"

    def get_redis_score(self, user_score):
        """
        Convert user score to Redis score based on scoring type.
        Redis sorted sets are ordered by score in ascending order,
        so we need to invert scores for highest-wins games.
        """
        if self.score_type == "lowest" or self.score_type == "time":
            return user_score
        # highest
        # For highest scores, we use negative values so Redis sorts correctly
        return -user_score
