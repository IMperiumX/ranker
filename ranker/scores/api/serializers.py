

from rest_framework import serializers

from ranker.games.api.serializers import GameListSerializer
from ranker.games.models import Game
from ranker.scores.models import Score
from ranker.users.api.serializers import UserSerializer


class ScoreSubmissionSerializer(serializers.Serializer):
    """Serializer for score submission."""

    game_id = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_game_id(self, value):
        """Validate that the game exists and is active."""
        try:
            game = Game.objects.get(id=value)
            if not game.is_active:
                raise serializers.ValidationError("This game is not currently active.")
            return value
        except Game.DoesNotExist:
            raise serializers.ValidationError("Game not found.")

    def validate_score(self, value):
        """Validate score value."""
        if value < 0:
            raise serializers.ValidationError("Score cannot be negative.")
        return value


class ScoreSerializer(serializers.ModelSerializer):
    """Serializer for Score model."""

    user = UserSerializer(read_only=True)
    game = GameListSerializer(read_only=True)

    class Meta:
        model = Score
        fields = [
            "id",
            "user",
            "game",
            "score",
            "submitted_at",
            "metadata",
        ]
        read_only_fields = ["id", "submitted_at"]


class ScoreHistorySerializer(serializers.ModelSerializer):
    """Simplified serializer for score history."""

    game_name = serializers.CharField(source="game.name", read_only=True)

    class Meta:
        model = Score
        fields = [
            "id",
            "game_name",
            "score",
            "submitted_at",
            "metadata",
        ]
        read_only_fields = ["id", "submitted_at"]


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for leaderboard entries."""

    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    score = serializers.DecimalField(max_digits=12, decimal_places=2)


class GlobalLeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for global leaderboard entries."""

    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    total_score = serializers.DecimalField(max_digits=12, decimal_places=2)


class UserRankSerializer(serializers.Serializer):
    """Serializer for user rank information."""

    user_rank = serializers.IntegerField()
    user_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_players = serializers.IntegerField()
    surrounding_players = LeaderboardEntrySerializer(many=True)


class ScoreSubmissionResponseSerializer(serializers.Serializer):
    """Serializer for score submission response."""

    message = serializers.CharField()
    score = serializers.DecimalField(max_digits=12, decimal_places=2)
    rank = serializers.IntegerField(required=False)
    total_players = serializers.IntegerField(required=False)
    is_personal_best = serializers.BooleanField(required=False)


class ReportTopPlayersSerializer(serializers.Serializer):
    """Serializer for top players report."""

    period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly"],
        default="weekly",
    )
    game_id = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=100)


class TopPlayerReportEntrySerializer(serializers.Serializer):
    """Serializer for top player report entries."""

    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    best_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_submissions = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    first_submission = serializers.DateTimeField()
    last_submission = serializers.DateTimeField()


# Advanced Reporting Serializers
class GamePerformanceSerializer(serializers.Serializer):
    """Serializer for individual game performance metrics."""

    game__id = serializers.IntegerField()
    game__name = serializers.CharField()
    game__score_type = serializers.CharField()
    total_plays = serializers.IntegerField()
    unique_players = serializers.IntegerField()
    avg_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    score_range = serializers.DecimalField(max_digits=12, decimal_places=2)
    first_play = serializers.DateTimeField()
    last_play = serializers.DateTimeField()


class TrendingDataSerializer(serializers.Serializer):
    """Serializer for trending data over time."""

    period = serializers.DateTimeField()
    total_submissions = serializers.IntegerField()
    unique_players = serializers.IntegerField()
    avg_score = serializers.DecimalField(max_digits=12, decimal_places=2)


class ScoreDistributionSerializer(serializers.Serializer):
    """Serializer for score distribution analysis."""

    total_scores = serializers.IntegerField()
    percentile_25 = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentile_50 = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentile_75 = serializers.DecimalField(max_digits=12, decimal_places=2)
    std_deviation = serializers.DecimalField(max_digits=12, decimal_places=2)


class GameAnalyticsSerializer(serializers.Serializer):
    """Serializer for comprehensive game analytics."""

    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    games_performance = GamePerformanceSerializer(many=True)
    trending_data = TrendingDataSerializer(many=True)
    score_distribution = ScoreDistributionSerializer()


class UserActivitySerializer(serializers.Serializer):
    """Serializer for user activity metrics."""

    user__id = serializers.IntegerField()
    user__email = serializers.CharField()
    user__name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    games_played = serializers.IntegerField()
    avg_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    best_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    first_activity = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    activity_span_days = serializers.DurationField()
    sessions_per_day = serializers.DecimalField(max_digits=10, decimal_places=2)


class EngagementTrendSerializer(serializers.Serializer):
    """Serializer for engagement trends over time."""

    period = serializers.DateTimeField()
    active_users = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    avg_session_length = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    retention_rate = serializers.IntegerField()


class NewVsReturningSerializer(serializers.Serializer):
    """Serializer for new vs returning users data."""

    date = serializers.DateField()
    new_users = serializers.IntegerField()
    returning_users = serializers.IntegerField()
    total_users = serializers.IntegerField()


class UserEngagementSerializer(serializers.Serializer):
    """Serializer for user engagement analytics."""

    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    user_activity = UserActivitySerializer(many=True)
    engagement_trends = EngagementTrendSerializer(many=True)
    new_vs_returning = NewVsReturningSerializer(many=True)


class ScoreProgressionSerializer(serializers.Serializer):
    """Serializer for individual user score progression."""

    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    score_history = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
        ),
    )
    improvement = serializers.DecimalField(max_digits=12, decimal_places=2)


class CompetitionMetricsSerializer(serializers.Serializer):
    """Serializer for competition intensity metrics."""

    total_participants = serializers.IntegerField()
    score_submissions = serializers.IntegerField()
    avg_submissions_per_user = serializers.DecimalField(max_digits=10, decimal_places=2)
    score_range = serializers.DecimalField(max_digits=12, decimal_places=2)
    leaderboard_volatility = serializers.IntegerField()


class LeaderboardTrendsSerializer(serializers.Serializer):
    """Serializer for leaderboard trends analysis."""

    game_id = serializers.IntegerField()
    game_name = serializers.CharField()
    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    current_leaderboard = LeaderboardEntrySerializer(many=True)
    score_progression = ScoreProgressionSerializer(many=True)
    competition_metrics = CompetitionMetricsSerializer()


class PeakHourSerializer(serializers.Serializer):
    """Serializer for peak activity hours."""

    hour = serializers.DateTimeField()
    submissions = serializers.IntegerField()


class ImprovementPatternSerializer(serializers.Serializer):
    """Serializer for score improvement patterns."""

    user_id = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    starting_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    ending_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    improvement = serializers.DecimalField(max_digits=12, decimal_places=2)
    consistency = serializers.DecimalField(max_digits=5, decimal_places=4)
    peak_score = serializers.DecimalField(max_digits=12, decimal_places=2)


class MetadataPatternSerializer(serializers.Serializer):
    """Serializer for metadata analysis patterns."""

    metadata__difficulty = serializers.CharField(allow_null=True)
    metadata__level = serializers.IntegerField(allow_null=True)
    avg_score = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class FrequencyPatternSerializer(serializers.Serializer):
    """Serializer for submission frequency patterns."""

    user_id = serializers.IntegerField()
    submission_count = serializers.IntegerField()
    days_active = serializers.IntegerField()
    avg_daily_submissions = serializers.DecimalField(max_digits=10, decimal_places=2)


class ScoringPatternsSerializer(serializers.Serializer):
    """Serializer for scoring patterns analysis."""

    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    peak_activity_hours = PeakHourSerializer(many=True)
    improvement_patterns = ImprovementPatternSerializer(many=True)
    metadata_patterns = MetadataPatternSerializer(many=True)
    frequency_patterns = FrequencyPatternSerializer(many=True)
