
import redis
from django.conf import settings
from django.contrib.auth import get_user_model

from ranker.games.models import Game

User = get_user_model()


class LeaderboardService:
    """
    Service class to handle Redis-based leaderboard operations.
    Uses Redis Sorted Sets for high-performance ranking queries.
    """

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(settings.REDIS_URL)

    def get_leaderboard_key(self, game_id: int) -> str:
        """Get Redis key for a game's leaderboard."""
        return f"leaderboard:{game_id}"

    def get_global_leaderboard_key(self) -> str:
        """Get Redis key for global leaderboard."""
        return "leaderboard:global"

    def update_user_score(self, game_id: int, user_id: int, score: float, game_score_type: str = "highest") -> None:
        """
        Update user's score in Redis leaderboard.

        Args:
            game_id: ID of the game
            user_id: ID of the user
            score: The score to set
            game_score_type: Type of scoring (highest, lowest, time)
        """
        game_key = self.get_leaderboard_key(game_id)
        global_key = self.get_global_leaderboard_key()

        # Convert score based on game type for Redis sorting
        redis_score = self._convert_score_for_redis(score, game_score_type)

        # Update game-specific leaderboard
        self.redis_client.zadd(game_key, {str(user_id): redis_score})

        # Update global leaderboard (use original score for global)
        self.redis_client.zadd(global_key, {str(user_id): score})

    def _convert_score_for_redis(self, score: float, game_score_type: str) -> float:
        """
        Convert score for Redis storage based on game type.
        Redis sorts in ascending order, so we need to handle different game types.
        """
        if game_score_type == "highest":
            # For highest scores, use negative values so Redis sorts correctly
            return -score
        # lowest or time
        return score

    def _convert_score_from_redis(self, redis_score: float, game_score_type: str) -> float:
        """Convert Redis score back to actual score."""
        if game_score_type == "highest":
            return -redis_score
        return redis_score

    def get_leaderboard(self, game_id: int, start: int = 0, end: int = 99) -> list[dict]:
        """
        Get leaderboard for a specific game.

        Args:
            game_id: ID of the game
            start: Starting rank (0-indexed)
            end: Ending rank (inclusive)

        Returns:
            List of dictionaries with user info and scores
        """
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return []

        game_key = self.get_leaderboard_key(game_id)

        # Get ranked users from Redis
        ranked_users = self.redis_client.zrevrange(
            game_key,
            start,
            end,
            withscores=True,
        )

        if not ranked_users:
            return []

        # Get user details from database
        user_ids = [int(user_id.decode()) for user_id, _ in ranked_users]
        users = User.objects.filter(id__in=user_ids)
        user_dict = {user.id: user for user in users}

        # Build leaderboard response
        leaderboard = []
        for rank, (user_id, redis_score) in enumerate(ranked_users, start=start + 1):
            user_id = int(user_id.decode())
            user = user_dict.get(user_id)

            if user:
                actual_score = self._convert_score_from_redis(redis_score, game.score_type)
                leaderboard.append({
                    "rank": rank,
                    "user_id": user_id,
                    "username": user.email,  # Using email as username
                    "name": user.name or user.email,
                    "score": actual_score,
                })

        return leaderboard

    def get_global_leaderboard(self, start: int = 0, end: int = 99) -> list[dict]:
        """
        Get global leaderboard across all games.

        Args:
            start: Starting rank (0-indexed)
            end: Ending rank (inclusive)

        Returns:
            List of dictionaries with user info and total scores
        """
        global_key = self.get_global_leaderboard_key()

        # Get ranked users from Redis
        ranked_users = self.redis_client.zrevrange(
            global_key,
            start,
            end,
            withscores=True,
        )

        if not ranked_users:
            return []

        # Get user details from database
        user_ids = [int(user_id.decode()) for user_id, _ in ranked_users]
        users = User.objects.filter(id__in=user_ids)
        user_dict = {user.id: user for user in users}

        # Build leaderboard response
        leaderboard = []
        for rank, (user_id, total_score) in enumerate(ranked_users, start=start + 1):
            user_id = int(user_id.decode())
            user = user_dict.get(user_id)

            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": user_id,
                    "username": user.email,
                    "name": user.name or user.email,
                    "total_score": total_score,
                })

        return leaderboard

    def get_user_rank(self, game_id: int, user_id: int) -> dict | None:
        """
        Get user's rank and surrounding players in a specific game.

        Args:
            game_id: ID of the game
            user_id: ID of the user

        Returns:
            Dictionary with user's rank info and surrounding players
        """
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None

        game_key = self.get_leaderboard_key(game_id)

        # Get user's rank (0-indexed)
        rank = self.redis_client.zrevrank(game_key, str(user_id))

        if rank is None:
            return None

        # Get user's score
        redis_score = self.redis_client.zscore(game_key, str(user_id))
        actual_score = self._convert_score_from_redis(redis_score, game.score_type)

        # Get surrounding players (5 above and 5 below)
        start_rank = max(0, rank - 5)
        end_rank = rank + 5

        surrounding_players = self.get_leaderboard(game_id, start_rank, end_rank)

        return {
            "user_rank": rank + 1,  # Convert to 1-indexed
            "user_score": actual_score,
            "surrounding_players": surrounding_players,
            "total_players": self.redis_client.zcard(game_key),
        }

    def get_user_global_rank(self, user_id: int) -> dict | None:
        """
        Get user's global rank across all games.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with user's global rank info
        """
        global_key = self.get_global_leaderboard_key()

        # Get user's rank (0-indexed)
        rank = self.redis_client.zrevrank(global_key, str(user_id))

        if rank is None:
            return None

        # Get user's total score
        total_score = self.redis_client.zscore(global_key, str(user_id))

        return {
            "user_rank": rank + 1,  # Convert to 1-indexed
            "total_score": total_score,
            "total_players": self.redis_client.zcard(global_key),
        }

    def clear_leaderboard(self, game_id: int) -> None:
        """Clear all scores for a specific game."""
        game_key = self.get_leaderboard_key(game_id)
        self.redis_client.delete(game_key)

    def clear_global_leaderboard(self) -> None:
        """Clear the global leaderboard."""
        global_key = self.get_global_leaderboard_key()
        self.redis_client.delete(global_key)

    def rebuild_leaderboard(self, game_id: int) -> None:
        """
        Rebuild leaderboard from database records.
        Useful for data consistency or recovery.
        """
        from .models import Score

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return

        # Clear existing leaderboard
        self.clear_leaderboard(game_id)

        # Get all best scores for this game
        user_scores = {}
        scores = Score.objects.filter(game=game).select_related("user")

        for score in scores:
            user_id = score.user.id
            current_score = float(score.score)

            if user_id not in user_scores:
                user_scores[user_id] = current_score
            elif game.score_type == "highest":
                user_scores[user_id] = max(user_scores[user_id], current_score)
            else:  # lowest or time
                user_scores[user_id] = min(user_scores[user_id], current_score)

        # Rebuild Redis leaderboard
        for user_id, score in user_scores.items():
            self.update_user_score(game_id, user_id, score, game.score_type)
