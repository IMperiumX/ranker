from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Score


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    """Admin interface for Score model."""

    list_display = [
        "user_email",
        "game_name",
        "score",
        "submitted_at",
        "view_metadata",
    ]

    list_filter = [
        "game",
        "submitted_at",
        "game__score_type",
    ]

    search_fields = [
        "user__email",
        "user__name",
        "game__name",
    ]

    readonly_fields = [
        "submitted_at",
        "view_metadata",
    ]

    date_hierarchy = "submitted_at"

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _("User Email")
    user_email.admin_order_field = "user__email"

    def game_name(self, obj):
        """Display game name."""
        return obj.game.name
    game_name.short_description = _("Game")
    game_name.admin_order_field = "game__name"

    def view_metadata(self, obj):
        """Display formatted metadata."""
        if obj.metadata:
            return format_html("<pre>{}</pre>", str(obj.metadata))
        return _("No metadata")
    view_metadata.short_description = _("Metadata")

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related("user", "game")

    # Admin actions
    actions = ["rebuild_leaderboard_for_selected_games"]

    def rebuild_leaderboard_for_selected_games(self, request, queryset):
        """Rebuild leaderboards for games related to selected scores."""
        from .services import LeaderboardService

        game_ids = queryset.values_list("game_id", flat=True).distinct()
        service = LeaderboardService()

        for game_id in game_ids:
            service.rebuild_leaderboard(game_id)

        self.message_user(
            request,
            _("Leaderboards rebuilt for {} games.").format(len(game_ids)),
        )

    rebuild_leaderboard_for_selected_games.short_description = _(
        "Rebuild leaderboards for related games",
    )
