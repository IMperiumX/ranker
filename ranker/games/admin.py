from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin interface for Game model."""

    list_display = [
        "name",
        "score_type",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "is_active",
        "score_type",
        "created_at",
    ]

    search_fields = [
        "name",
        "description",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {
            "fields": ("name", "description", "is_active"),
        }),
        (_("Scoring Configuration"), {
            "fields": ("score_type",),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request)
