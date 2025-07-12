from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ScoresConfig(AppConfig):
    """Scores app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ranker.scores"
    verbose_name = _("Scores")

    def ready(self):
        """Run when the app is ready."""
