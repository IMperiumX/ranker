from datetime import timedelta

from django.db.models import Avg
from django.db.models import Count
from django.db.models import F
from django.db.models import Max
from django.db.models import Min
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncHour
from django.db.models.functions import TruncMonth
from django.db.models.functions import TruncWeek
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ranker.games.models import Game
from ranker.scores.models import Score
from ranker.scores.services import LeaderboardService
from ranker.users.models import User

from .serializers import GameAnalyticsSerializer
from .serializers import GlobalLeaderboardEntrySerializer
from .serializers import LeaderboardEntrySerializer
from .serializers import LeaderboardTrendsSerializer
from .serializers import ScoreHistorySerializer
from .serializers import ScoreSerializer
from .serializers import ScoreSubmissionSerializer
from .serializers import ScoringPatternsSerializer
from .serializers import TopPlayerReportEntrySerializer
from .serializers import UserEngagementSerializer
from .serializers import UserRankSerializer


@method_decorator(ratelimit(key="user", rate="30/m", method="POST", block=True), name="post")
class ScoreSubmissionView(APIView):
    """
    API endpoint for submitting scores.
    POST /api/scores/
    Rate limited to 30 submissions per minute per user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Submit a score for a specific game."""
        serializer = ScoreSubmissionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        game_id = serializer.validated_data["game_id"]
        score_value = serializer.validated_data["score"]
        metadata = serializer.validated_data.get("metadata", {})

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {"error": "Game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create score record
        score_obj = Score.objects.create(
            user=request.user,
            game=game,
            score=score_value,
            metadata=metadata,
        )

        # Get user's rank after submission
        leaderboard_service = LeaderboardService()
        rank_info = leaderboard_service.get_user_rank(game_id, request.user.id)

        # Check if this is a personal best
        previous_best = Score.get_user_best_score(request.user, game)
        is_personal_best = False

        if previous_best:
            if game.score_type == "highest":
                is_personal_best = score_value > previous_best.score
            else:  # lowest or time
                is_personal_best = score_value < previous_best.score
        else:
            is_personal_best = True

        response_data = {
            "message": "Score submitted successfully",
            "score": score_value,
            "is_personal_best": is_personal_best,
        }

        if rank_info:
            response_data.update({
                "rank": rank_info["user_rank"],
                "total_players": rank_info["total_players"],
            })

        return Response(response_data, status=status.HTTP_201_CREATED)


class LeaderboardView(APIView):
    """
    API endpoint for viewing leaderboards.
    GET /api/leaderboard/{game_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        """Get leaderboard for a specific game."""
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {"error": "Game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get pagination parameters
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)  # Max 100 per page

        start = (page - 1) * page_size
        end = start + page_size - 1

        # Get leaderboard from Redis
        leaderboard_service = LeaderboardService()
        leaderboard = leaderboard_service.get_leaderboard(game_id, start, end)

        # Serialize the data
        serializer = LeaderboardEntrySerializer(leaderboard, many=True)

        return Response({
            "game_id": game_id,
            "game_name": game.name,
            "leaderboard": serializer.data,
            "page": page,
            "page_size": page_size,
            "has_next": len(leaderboard) == page_size,
        })


class GlobalLeaderboardView(APIView):
    """
    API endpoint for viewing global leaderboard.
    GET /api/leaderboard/global/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get global leaderboard across all games."""
        # Get pagination parameters
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)  # Max 100 per page

        start = (page - 1) * page_size
        end = start + page_size - 1

        # Get global leaderboard from Redis
        leaderboard_service = LeaderboardService()
        leaderboard = leaderboard_service.get_global_leaderboard(start, end)

        # Serialize the data
        serializer = GlobalLeaderboardEntrySerializer(leaderboard, many=True)

        return Response({
            "leaderboard": serializer.data,
            "page": page,
            "page_size": page_size,
            "has_next": len(leaderboard) == page_size,
        })


class UserRankView(APIView):
    """
    API endpoint for getting user's rank.
    GET /api/leaderboard/{game_id}/my-rank/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        """Get user's rank and surrounding players."""
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {"error": "Game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        leaderboard_service = LeaderboardService()
        rank_info = leaderboard_service.get_user_rank(game_id, request.user.id)

        if not rank_info:
            return Response(
                {"error": "User not ranked in this game"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserRankSerializer(rank_info)
        return Response(serializer.data)


class ScoreHistoryView(APIView):
    """
    API endpoint for viewing user's score history.
    GET /api/scores/history/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's score history."""
        game_id = request.query_params.get("game_id")

        if not game_id:
            return Response(
                {"error": "game_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {"error": "Game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get user's score history
        scores = Score.objects.filter(
            user=request.user,
            game=game,
        ).order_by("-submitted_at")

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)

        start = (page - 1) * page_size
        end = start + page_size

        paginated_scores = scores[start:end]

        serializer = ScoreHistorySerializer(paginated_scores, many=True)

        return Response({
            "game_id": game_id,
            "game_name": game.name,
            "scores": serializer.data,
            "page": page,
            "page_size": page_size,
            "has_next": len(paginated_scores) == page_size,
        })


class TopPlayersReportView(APIView):
    """
    API endpoint for admin reports of top players.
    GET /api/reports/top-players/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate top players report."""
        period = request.query_params.get("period", "weekly")
        game_id = request.query_params.get("game_id")
        limit = int(request.query_params.get("limit", 10))
        limit = min(limit, 100)  # Max 100 results

        # Calculate date range
        now = timezone.now()
        if period == "daily":
            start_date = now - timedelta(days=1)
        elif period == "weekly":
            start_date = now - timedelta(weeks=1)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        else:
            return Response(
                {"error": "Invalid period. Must be daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build query
        query = Q(submitted_at__gte=start_date)

        if game_id:
            try:
                game = Game.objects.get(id=game_id)
                query &= Q(game=game)
            except Game.DoesNotExist:
                return Response(
                    {"error": "Game not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Get top players statistics
        top_players = (
            Score.objects.filter(query)
            .values("user__id", "user__email", "user__name", "game__score_type")
            .annotate(
                total_submissions=Count("id"),
                best_score=Max("score"),
                average_score=Avg("score"),
                first_submission=Min("submitted_at"),
                last_submission=Max("submitted_at"),
            )
            .order_by("-best_score")[:limit]
        )

        # Format response
        report_data = []
        for rank, player in enumerate(top_players, 1):
            report_data.append({
                "rank": rank,
                "user_id": player["user__id"],
                "username": player["user__email"],
                "name": player["user__name"] or player["user__email"],
                "best_score": player["best_score"],
                "total_submissions": player["total_submissions"],
                "average_score": player["average_score"],
                "first_submission": player["first_submission"],
                "last_submission": player["last_submission"],
            })

        serializer = TopPlayerReportEntrySerializer(report_data, many=True)

        return Response({
            "period": period,
            "game_id": game_id,
            "start_date": start_date,
            "end_date": now,
            "total_results": len(report_data),
            "top_players": serializer.data,
        })


class GameAnalyticsView(APIView):
    """
    Advanced analytics for game performance and statistics.
    GET /api/reports/game-analytics/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate comprehensive game analytics."""
        period = request.query_params.get("period", "weekly")
        game_id = request.query_params.get("game_id")

        # Calculate date range
        now = timezone.now()
        if period == "daily":
            start_date = now - timedelta(days=7)  # Last 7 days for daily view
            trunc_func = TruncDate
        elif period == "weekly":
            start_date = now - timedelta(weeks=12)  # Last 12 weeks
            trunc_func = TruncWeek
        elif period == "monthly":
            start_date = now - timedelta(days=365)  # Last year
            trunc_func = TruncMonth
        else:
            return Response(
                {"error": "Invalid period. Must be daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = Q(submitted_at__gte=start_date)
        if game_id:
            try:
                game = Game.objects.get(id=game_id)
                query &= Q(game=game)
            except Game.DoesNotExist:
                return Response(
                    {"error": "Game not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Game performance metrics
        games_stats = (
            Score.objects.filter(query)
            .values("game__id", "game__name", "game__score_type")
            .annotate(
                total_plays=Count("id"),
                unique_players=Count("user", distinct=True),
                avg_score=Avg("score"),
                max_score=Max("score"),
                min_score=Min("score"),
                score_range=F("max_score") - F("min_score"),
                first_play=Min("submitted_at"),
                last_play=Max("submitted_at"),
            )
            .order_by("-total_plays")
        )

        # Trending data over time
        trending_data = (
            Score.objects.filter(query)
            .annotate(period=trunc_func("submitted_at"))
            .values("period")
            .annotate(
                total_submissions=Count("id"),
                unique_players=Count("user", distinct=True),
                avg_score=Avg("score"),
            )
            .order_by("period")
        )

        # Score distribution analysis
        score_distribution = (
            Score.objects.filter(query)
            .aggregate(
                total_scores=Count("id"),
                percentile_25=Min("score"),  # Simplified - would need proper percentile calc
                percentile_50=Avg("score"),
                percentile_75=Max("score"),
                std_deviation=Avg("score"),  # Simplified
            )
        )

        serializer = GameAnalyticsSerializer({
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "games_performance": games_stats,
            "trending_data": trending_data,
            "score_distribution": score_distribution,
        })

        return Response(serializer.data)


class UserEngagementView(APIView):
    """
    User engagement and retention analytics.
    GET /api/reports/user-engagement/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate user engagement analytics."""
        period = request.query_params.get("period", "weekly")

        # Calculate date range
        now = timezone.now()
        if period == "daily":
            start_date = now - timedelta(days=30)
            trunc_func = TruncDate
        elif period == "weekly":
            start_date = now - timedelta(weeks=12)
            trunc_func = TruncWeek
        elif period == "monthly":
            start_date = now - timedelta(days=365)
            trunc_func = TruncMonth
        else:
            return Response(
                {"error": "Invalid period. Must be daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # User activity metrics
        user_activity = (
            Score.objects.filter(submitted_at__gte=start_date)
            .values("user__id", "user__email", "user__name")
            .annotate(
                total_sessions=Count("id"),
                games_played=Count("game", distinct=True),
                avg_score=Avg("score"),
                best_score=Max("score"),
                first_activity=Min("submitted_at"),
                last_activity=Max("submitted_at"),
                activity_span_days=(Max("submitted_at") - Min("submitted_at")),
                sessions_per_day=Count("id") / (Max("submitted_at") - Min("submitted_at")).total_seconds() * 86400,
            )
            .order_by("-total_sessions")[:50]  # Top 50 most active users
        )

        # Engagement trends over time
        engagement_trends = (
            Score.objects.filter(submitted_at__gte=start_date)
            .annotate(period=trunc_func("submitted_at"))
            .values("period")
            .annotate(
                active_users=Count("user", distinct=True),
                total_sessions=Count("id"),
                avg_session_length=Avg("metadata__time_played"),  # If available in metadata
                retention_rate=Count("user", distinct=True),  # Simplified metric
            )
            .order_by("period")
        )

        # New vs returning users
        new_vs_returning = []
        for days_ago in range(7):
            date = now - timedelta(days=days_ago)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)

            daily_users = User.objects.filter(
                scores__submitted_at__gte=date_start,
                scores__submitted_at__lt=date_end,
            ).distinct()

            new_users = daily_users.filter(date_joined__gte=date_start)
            returning_users = daily_users.exclude(date_joined__gte=date_start)

            new_vs_returning.append({
                "date": date_start.date(),
                "new_users": new_users.count(),
                "returning_users": returning_users.count(),
                "total_users": daily_users.count(),
            })

        serializer = UserEngagementSerializer({
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "user_activity": user_activity,
            "engagement_trends": engagement_trends,
            "new_vs_returning": new_vs_returning,
        })

        return Response(serializer.data)


class LeaderboardTrendsView(APIView):
    """
    Leaderboard movement and ranking trends analysis.
    GET /api/reports/leaderboard-trends/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate leaderboard trends analysis."""
        game_id = request.query_params.get("game_id")
        period = request.query_params.get("period", "weekly")

        if not game_id:
            return Response(
                {"error": "game_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {"error": "Game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate date range
        now = timezone.now()
        if period == "daily":
            start_date = now - timedelta(days=30)
        elif period == "weekly":
            start_date = now - timedelta(weeks=12)
        elif period == "monthly":
            start_date = now - timedelta(days=365)
        else:
            return Response(
                {"error": "Invalid period. Must be daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get current Redis leaderboard
        leaderboard_service = LeaderboardService()
        current_leaderboard = leaderboard_service.get_leaderboard(game_id, 0, 99)

        # Historical score progression for top players
        top_user_ids = [player["user_id"] for player in current_leaderboard[:10]]

        score_progression = []
        for user_id in top_user_ids:
            user_scores = (
                Score.objects.filter(
                    user_id=user_id,
                    game=game,
                    submitted_at__gte=start_date,
                )
                .order_by("submitted_at")
                .values("submitted_at", "score")
            )

            if user_scores:
                user = User.objects.get(id=user_id)
                score_progression.append({
                    "user_id": user_id,
                    "username": user.email,
                    "name": user.name or user.email,
                    "score_history": list(user_scores),
                    "improvement": (
                        list(user_scores)[-1]["score"] - list(user_scores)[0]["score"]
                        if len(user_scores) > 1 else 0
                    ),
                })

        # Competition intensity metrics
        competition_metrics = (
            Score.objects.filter(game=game, submitted_at__gte=start_date)
            .aggregate(
                total_participants=Count("user", distinct=True),
                score_submissions=Count("id"),
                avg_submissions_per_user=Count("id") / Count("user", distinct=True),
                score_range=Max("score") - Min("score"),
                leaderboard_volatility=Count("user", distinct=True),  # Simplified
            )
        )

        serializer = LeaderboardTrendsSerializer({
            "game_id": game_id,
            "game_name": game.name,
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "current_leaderboard": current_leaderboard[:10],
            "score_progression": score_progression,
            "competition_metrics": competition_metrics,
        })

        return Response(serializer.data)


class ScoringPatternsView(APIView):
    """
    Advanced scoring patterns and behavioral analysis.
    GET /api/reports/scoring-patterns/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate scoring patterns analysis."""
        period = request.query_params.get("period", "weekly")
        game_id = request.query_params.get("game_id")

        # Calculate date range
        now = timezone.now()
        if period == "daily":
            start_date = now - timedelta(days=7)
        elif period == "weekly":
            start_date = now - timedelta(weeks=4)
        elif period == "monthly":
            start_date = now - timedelta(days=90)
        else:
            return Response(
                {"error": "Invalid period. Must be daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = Q(submitted_at__gte=start_date)
        if game_id:
            query &= Q(game_id=game_id)

        # Peak activity hours
        peak_hours = (
            Score.objects.filter(query)
            .annotate(hour=TruncHour("submitted_at"))
            .values("hour")
            .annotate(submissions=Count("id"))
            .order_by("-submissions")[:24]
        )

        # Score improvement patterns
        improvement_patterns = []
        active_users = (
            Score.objects.filter(query)
            .values_list("user_id", flat=True)
            .distinct()
        )

        for user_id in list(active_users)[:20]:  # Top 20 for performance
            user_scores = (
                Score.objects.filter(user_id=user_id, submitted_at__gte=start_date)
                .order_by("submitted_at")
                .values_list("score", flat=True)
            )

            if len(user_scores) > 1:
                scores_list = list(user_scores)
                improvement_pattern = {
                    "user_id": user_id,
                    "total_sessions": len(scores_list),
                    "starting_score": scores_list[0],
                    "ending_score": scores_list[-1],
                    "improvement": scores_list[-1] - scores_list[0],
                    "consistency": len([s for s in scores_list if s >= scores_list[0]]) / len(scores_list),
                    "peak_score": max(scores_list),
                }
                improvement_patterns.append(improvement_pattern)

        # Metadata analysis (if available)
        metadata_patterns = (
            Score.objects.filter(query)
            .exclude(metadata={})
            .values("metadata__difficulty", "metadata__level")
            .annotate(
                avg_score=Avg("score"),
                count=Count("id"),
            )
            .order_by("-count")[:10]
        )

        # Submission frequency patterns
        frequency_patterns = (
            Score.objects.filter(query)
            .values("user_id")
            .annotate(
                submission_count=Count("id"),
                days_active=Count("submitted_at__date", distinct=True),
                avg_daily_submissions=Count("id") / Count("submitted_at__date", distinct=True),
            )
            .filter(submission_count__gte=5)  # Users with at least 5 submissions
            .order_by("-avg_daily_submissions")[:20]
        )

        serializer = ScoringPatternsSerializer({
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "peak_activity_hours": peak_hours,
            "improvement_patterns": improvement_patterns,
            "metadata_patterns": metadata_patterns,
            "frequency_patterns": frequency_patterns,
        })

        return Response(serializer.data)


class ScoreViewSet(ListModelMixin, GenericViewSet):
    """
    ViewSet for Score model operations.
    """

    serializer_class = ScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get scores for the current user."""
        return Score.objects.filter(user=self.request.user).select_related("game")

    @action(detail=False, methods=["post"])
    def submit(self, request):
        """Submit a score - delegated to ScoreSubmissionView."""
        view = ScoreSubmissionView()
        view.request = request
        return view.post(request)

    @action(detail=False, methods=["get"])
    def history(self, request):
        """Get score history - delegated to ScoreHistoryView."""
        view = ScoreHistoryView()
        view.request = request
        return view.get(request)
