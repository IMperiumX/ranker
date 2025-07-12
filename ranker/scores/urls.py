from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .api.views import GameAnalyticsView
from .api.views import GlobalLeaderboardView
from .api.views import LeaderboardTrendsView
from .api.views import LeaderboardView
from .api.views import ScoreHistoryView
from .api.views import ScoreSubmissionView
from .api.views import ScoreViewSet
from .api.views import ScoringPatternsView
from .api.views import TopPlayersReportView
from .api.views import UserEngagementView
from .api.views import UserRankView

# Create router for ViewSets
router = DefaultRouter()
router.register(r"scores", ScoreViewSet, basename="scores")

# URL patterns
urlpatterns = [
    # Score submission
    path("scores/", ScoreSubmissionView.as_view(), name="score-submission"),

    # Leaderboards
    path("leaderboard/<int:game_id>/", LeaderboardView.as_view(), name="leaderboard"),
    path("leaderboard/global/", GlobalLeaderboardView.as_view(), name="global-leaderboard"),
    path("leaderboard/<int:game_id>/my-rank/", UserRankView.as_view(), name="user-rank"),

    # Score history
    path("scores/history/", ScoreHistoryView.as_view(), name="score-history"),

    # Basic admin reports
    path("reports/top-players/", TopPlayersReportView.as_view(), name="top-players-report"),

    # Advanced analytics and reporting
    path("reports/game-analytics/", GameAnalyticsView.as_view(), name="game-analytics"),
    path("reports/user-engagement/", UserEngagementView.as_view(), name="user-engagement"),
    path("reports/leaderboard-trends/", LeaderboardTrendsView.as_view(), name="leaderboard-trends"),
    path("reports/scoring-patterns/", ScoringPatternsView.as_view(), name="scoring-patterns"),

    # Include router URLs
    path("", include(router.urls)),
]
