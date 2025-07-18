from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GamesConfig(AppConfig):
    """Games app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ranker.games"
    verbose_name = _("Games")

    def ready(self):
        """Run when the app is ready."""
