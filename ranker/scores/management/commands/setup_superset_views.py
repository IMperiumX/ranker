import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Set up database views for Apache Superset analytics and dashboards"

    def add_arguments(self, parser):
        parser.add_argument(
            "--drop-existing",
            action="store_true",
            help="Drop existing views before creating new ones",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up Apache Superset database views..."))

        if options["drop_existing"]:
            self.drop_existing_views()

        # Create all views
        self.create_game_analytics_view()
        self.create_user_engagement_view()
        self.create_leaderboard_trends_view()
        self.create_scoring_patterns_view()
        self.create_daily_metrics_view()
        self.create_user_performance_view()
        self.create_game_popularity_view()

        self.stdout.write(self.style.SUCCESS("✅ All Superset views created successfully!"))
        self.show_views_summary()

    def drop_existing_views(self):
        """Drop existing views."""
        self.stdout.write("Dropping existing views...")

        views_to_drop = [
            "superset_game_analytics",
            "superset_user_engagement",
            "superset_leaderboard_trends",
            "superset_scoring_patterns",
            "superset_daily_metrics",
            "superset_user_performance",
            "superset_game_popularity",
        ]

        with connection.cursor() as cursor:
            for view_name in views_to_drop:
                try:
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
                    self.stdout.write(f"  ✓ Dropped {view_name}")
                except Exception as e:
                    self.stdout.write(f"  ⚠️  Could not drop {view_name}: {e}")

    def create_game_analytics_view(self):
        """Create game analytics view for Superset."""
        self.stdout.write("Creating game analytics view...")

        sql = """
        CREATE OR REPLACE VIEW superset_game_analytics AS
        SELECT
            g.id as game_id,
            g.name as game_name,
            g.score_type,
            g.is_active,
            g.created_at as game_created_at,
            COUNT(s.id) as total_submissions,
            COUNT(DISTINCT s.user_id) as unique_players,
            AVG(s.score) as avg_score,
            MAX(s.score) as max_score,
            MIN(s.score) as min_score,
            STDDEV(s.score) as score_stddev,
            MAX(s.score) - MIN(s.score) as score_range,
            MIN(s.submitted_at) as first_submission,
            MAX(s.submitted_at) as last_submission,
            EXTRACT(EPOCH FROM (MAX(s.submitted_at) - MIN(s.submitted_at)))/86400 as activity_days,
            COUNT(s.id)::float / NULLIF(COUNT(DISTINCT s.user_id), 0) as submissions_per_player,
            COUNT(s.id)::float / NULLIF(EXTRACT(EPOCH FROM (MAX(s.submitted_at) - MIN(s.submitted_at)))/86400, 0) as submissions_per_day
        FROM games_game g
        LEFT JOIN scores_score s ON g.id = s.game_id
        GROUP BY g.id, g.name, g.score_type, g.is_active, g.created_at
        ORDER BY total_submissions DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ Game analytics view created")

    def create_user_engagement_view(self):
        """Create user engagement view for Superset."""
        self.stdout.write("Creating user engagement view...")

        sql = """
        CREATE OR REPLACE VIEW superset_user_engagement AS
        SELECT
            u.id as user_id,
            u.email as user_email,
            u.name as user_name,
            u.date_joined,
            u.is_active as user_is_active,
            COUNT(s.id) as total_submissions,
            COUNT(DISTINCT s.game_id) as games_played,
            AVG(s.score) as avg_score,
            MAX(s.score) as best_score,
            MIN(s.score) as worst_score,
            MIN(s.submitted_at) as first_submission,
            MAX(s.submitted_at) as last_submission,
            EXTRACT(EPOCH FROM (MAX(s.submitted_at) - MIN(s.submitted_at)))/86400 as activity_span_days,
            COUNT(DISTINCT DATE(s.submitted_at)) as active_days,
            COUNT(s.id)::float / NULLIF(COUNT(DISTINCT DATE(s.submitted_at)), 0) as submissions_per_active_day,
            CASE
                WHEN MAX(s.submitted_at) >= NOW() - INTERVAL '7 days' THEN 'Active'
                WHEN MAX(s.submitted_at) >= NOW() - INTERVAL '30 days' THEN 'Recent'
                ELSE 'Inactive'
            END as user_status,
            EXTRACT(EPOCH FROM (NOW() - MAX(s.submitted_at)))/86400 as days_since_last_activity
        FROM users_user u
        LEFT JOIN scores_score s ON u.id = s.user_id
        GROUP BY u.id, u.email, u.name, u.date_joined, u.is_active
        ORDER BY total_submissions DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ User engagement view created")

    def create_leaderboard_trends_view(self):
        """Create leaderboard trends view for Superset."""
        self.stdout.write("Creating leaderboard trends view...")

        sql = """
        CREATE OR REPLACE VIEW superset_leaderboard_trends AS
        SELECT
            s.game_id,
            g.name as game_name,
            g.score_type,
            s.user_id,
            u.email as user_email,
            u.name as user_name,
            s.score,
            s.submitted_at,
            DATE(s.submitted_at) as submission_date,
            EXTRACT(HOUR FROM s.submitted_at) as submission_hour,
            EXTRACT(DOW FROM s.submitted_at) as day_of_week,
            EXTRACT(WEEK FROM s.submitted_at) as week_number,
            EXTRACT(MONTH FROM s.submitted_at) as month,
            RANK() OVER (PARTITION BY s.game_id, DATE(s.submitted_at) ORDER BY
                CASE WHEN g.score_type = 'highest' THEN s.score END DESC,
                CASE WHEN g.score_type IN ('lowest', 'time') THEN s.score END ASC
            ) as daily_rank,
            ROW_NUMBER() OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) as user_submission_sequence,
            LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) as previous_score,
            s.score - LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) as score_improvement,
            CASE
                WHEN LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) IS NULL THEN 'First'
                WHEN (g.score_type = 'highest' AND s.score > LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at)) THEN 'Better'
                WHEN (g.score_type IN ('lowest', 'time') AND s.score < LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at)) THEN 'Better'
                WHEN s.score = LAG(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) THEN 'Same'
                ELSE 'Worse'
            END as performance_trend
        FROM scores_score s
        JOIN games_game g ON s.game_id = g.id
        JOIN users_user u ON s.user_id = u.id
        ORDER BY s.submitted_at DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ Leaderboard trends view created")

    def create_scoring_patterns_view(self):
        """Create scoring patterns view for Superset."""
        self.stdout.write("Creating scoring patterns view...")

        sql = """
        CREATE OR REPLACE VIEW superset_scoring_patterns AS
        SELECT
            DATE_TRUNC('hour', s.submitted_at) as hour_bucket,
            DATE(s.submitted_at) as submission_date,
            EXTRACT(HOUR FROM s.submitted_at) as hour_of_day,
            EXTRACT(DOW FROM s.submitted_at) as day_of_week,
            CASE EXTRACT(DOW FROM s.submitted_at)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_name,
            CASE
                WHEN EXTRACT(HOUR FROM s.submitted_at) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN EXTRACT(HOUR FROM s.submitted_at) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN EXTRACT(HOUR FROM s.submitted_at) BETWEEN 18 AND 23 THEN 'Evening'
                ELSE 'Night'
            END as time_period,
            s.game_id,
            g.name as game_name,
            g.score_type,
            COUNT(*) as submission_count,
            COUNT(DISTINCT s.user_id) as unique_users,
            AVG(s.score) as avg_score,
            MAX(s.score) as max_score,
            MIN(s.score) as min_score,
            STDDEV(s.score) as score_stddev,
            COALESCE(AVG((s.metadata->>'level')::int), 0) as avg_level,
            COALESCE(AVG((s.metadata->>'time_played')::int), 0) as avg_time_played,
            COUNT(*) FILTER (WHERE s.metadata->>'difficulty' = 'easy') as easy_count,
            COUNT(*) FILTER (WHERE s.metadata->>'difficulty' = 'medium') as medium_count,
            COUNT(*) FILTER (WHERE s.metadata->>'difficulty' = 'hard') as hard_count
        FROM scores_score s
        JOIN games_game g ON s.game_id = g.id
        GROUP BY
            DATE_TRUNC('hour', s.submitted_at),
            DATE(s.submitted_at),
            EXTRACT(HOUR FROM s.submitted_at),
            EXTRACT(DOW FROM s.submitted_at),
            s.game_id,
            g.name,
            g.score_type
        ORDER BY hour_bucket DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ Scoring patterns view created")

    def create_daily_metrics_view(self):
        """Create daily metrics view for Superset."""
        self.stdout.write("Creating daily metrics view...")

        sql = """
        CREATE OR REPLACE VIEW superset_daily_metrics AS
        SELECT
            DATE(s.submitted_at) as metric_date,
            COUNT(*) as total_submissions,
            COUNT(DISTINCT s.user_id) as daily_active_users,
            COUNT(DISTINCT s.game_id) as games_with_activity,
            AVG(s.score) as avg_score,
            COUNT(DISTINCT s.user_id) FILTER (WHERE u.date_joined::date = DATE(s.submitted_at)) as new_users_active,
            COUNT(DISTINCT s.user_id) FILTER (WHERE u.date_joined::date < DATE(s.submitted_at)) as returning_users_active,
            COUNT(*) / COUNT(DISTINCT s.user_id) as avg_submissions_per_user,
            MAX(s.score) as daily_high_score,
            COUNT(DISTINCT CASE WHEN
                ROW_NUMBER() OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) = 1
                THEN s.user_id
            END) as new_players_to_games,
            EXTRACT(DOW FROM s.submitted_at) as day_of_week,
            CASE EXTRACT(DOW FROM s.submitted_at)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_name,
            CASE
                WHEN EXTRACT(DOW FROM s.submitted_at) IN (0, 6) THEN 'Weekend'
                ELSE 'Weekday'
            END as day_type
        FROM scores_score s
        JOIN users_user u ON s.user_id = u.id
        GROUP BY DATE(s.submitted_at), EXTRACT(DOW FROM s.submitted_at)
        ORDER BY metric_date DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ Daily metrics view created")

    def create_user_performance_view(self):
        """Create user performance view for Superset."""
        self.stdout.write("Creating user performance view...")

        sql = """
        CREATE OR REPLACE VIEW superset_user_performance AS
        WITH user_stats AS (
            SELECT
                s.user_id,
                s.game_id,
                u.email as user_email,
                u.name as user_name,
                g.name as game_name,
                g.score_type,
                COUNT(*) as total_attempts,
                CASE WHEN g.score_type = 'highest' THEN MAX(s.score) ELSE MIN(s.score) END as best_score,
                CASE WHEN g.score_type = 'highest' THEN MIN(s.score) ELSE MAX(s.score) END as worst_score,
                AVG(s.score) as avg_score,
                STDDEV(s.score) as score_consistency,
                MIN(s.submitted_at) as first_attempt,
                MAX(s.submitted_at) as last_attempt,
                FIRST_VALUE(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at) as first_score,
                LAST_VALUE(s.score) OVER (PARTITION BY s.user_id, s.game_id ORDER BY s.submitted_at ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as latest_score
            FROM scores_score s
            JOIN users_user u ON s.user_id = u.id
            JOIN games_game g ON s.game_id = g.id
            GROUP BY s.user_id, s.game_id, u.email, u.name, g.name, g.score_type
        )
        SELECT
            *,
            latest_score - first_score as score_improvement,
            CASE
                WHEN score_type = 'highest' AND latest_score > first_score THEN 'Improving'
                WHEN score_type IN ('lowest', 'time') AND latest_score < first_score THEN 'Improving'
                WHEN latest_score = first_score THEN 'Stable'
                ELSE 'Declining'
            END as improvement_trend,
            CASE
                WHEN total_attempts = 1 THEN 'Beginner'
                WHEN total_attempts <= 5 THEN 'Casual'
                WHEN total_attempts <= 20 THEN 'Regular'
                ELSE 'Dedicated'
            END as player_type,
            EXTRACT(EPOCH FROM (last_attempt - first_attempt))/86400 as playing_period_days,
            total_attempts::float / NULLIF(EXTRACT(EPOCH FROM (last_attempt - first_attempt))/86400, 0) as attempts_per_day
        FROM user_stats
        ORDER BY total_attempts DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ User performance view created")

    def create_game_popularity_view(self):
        """Create game popularity view for Superset."""
        self.stdout.write("Creating game popularity view...")

        sql = """
        CREATE OR REPLACE VIEW superset_game_popularity AS
        WITH weekly_stats AS (
            SELECT
                g.id as game_id,
                g.name as game_name,
                g.score_type,
                DATE_TRUNC('week', s.submitted_at) as week_start,
                COUNT(*) as weekly_submissions,
                COUNT(DISTINCT s.user_id) as weekly_players,
                AVG(s.score) as weekly_avg_score,
                COUNT(DISTINCT s.user_id) FILTER (WHERE
                    NOT EXISTS (
                        SELECT 1 FROM scores_score s2
                        WHERE s2.user_id = s.user_id
                        AND s2.game_id = s.game_id
                        AND s2.submitted_at < DATE_TRUNC('week', s.submitted_at)
                    )
                ) as new_players_this_week,
                RANK() OVER (PARTITION BY DATE_TRUNC('week', s.submitted_at) ORDER BY COUNT(*) DESC) as weekly_popularity_rank
            FROM games_game g
            LEFT JOIN scores_score s ON g.id = s.game_id
            WHERE s.submitted_at IS NOT NULL
            GROUP BY g.id, g.name, g.score_type, DATE_TRUNC('week', s.submitted_at)
        ),
        overall_stats AS (
            SELECT
                g.id as game_id,
                g.name as game_name,
                COUNT(*) as total_submissions,
                COUNT(DISTINCT s.user_id) as total_players,
                MIN(s.submitted_at) as first_activity,
                MAX(s.submitted_at) as last_activity,
                EXTRACT(EPOCH FROM (MAX(s.submitted_at) - MIN(s.submitted_at)))/604800 as active_weeks
            FROM games_game g
            LEFT JOIN scores_score s ON g.id = s.game_id
            WHERE s.submitted_at IS NOT NULL
            GROUP BY g.id, g.name
        )
        SELECT
            ws.*,
            os.total_submissions,
            os.total_players,
            os.first_activity,
            os.last_activity,
            os.active_weeks,
            CASE
                WHEN ws.weekly_popularity_rank <= 3 THEN 'Top'
                WHEN ws.weekly_popularity_rank <= 10 THEN 'Popular'
                ELSE 'Niche'
            END as popularity_tier,
            ws.weekly_submissions::float / NULLIF(ws.weekly_players, 0) as submissions_per_player_per_week,
            ws.new_players_this_week::float / NULLIF(ws.weekly_players, 0) as new_player_ratio
        FROM weekly_stats ws
        JOIN overall_stats os ON ws.game_id = os.game_id
        ORDER BY ws.week_start DESC, ws.weekly_submissions DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

        self.stdout.write("  ✓ Game popularity view created")

    def show_views_summary(self):
        """Show summary of created views."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("APACHE SUPERSET VIEWS SUMMARY"))
        self.stdout.write("="*60)

        views_info = [
            ("superset_game_analytics", "Game performance metrics and statistics"),
            ("superset_user_engagement", "User activity and engagement patterns"),
            ("superset_leaderboard_trends", "Leaderboard movements and ranking trends"),
            ("superset_scoring_patterns", "Scoring patterns by time and difficulty"),
            ("superset_daily_metrics", "Daily activity and user metrics"),
            ("superset_user_performance", "Individual user performance analysis"),
            ("superset_game_popularity", "Game popularity and growth trends"),
        ]

        for view_name, description in views_info:
            self.stdout.write(f"📊 {view_name}: {description}")

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Next Steps:"))
        self.stdout.write("1. Start Superset: docker-compose -f docker-compose.superset.yml up -d")
        self.stdout.write("2. Access Superset: http://localhost:8088")
        self.stdout.write("3. Login: admin / admin")
        self.stdout.write("4. Add database connection to your leaderboard database")
        self.stdout.write("5. Create datasets from the views above")
        self.stdout.write("6. Build amazing dashboards!")
        self.stdout.write("="*60)
