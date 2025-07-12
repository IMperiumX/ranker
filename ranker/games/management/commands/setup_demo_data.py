import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from ranker.games.models import Game
from ranker.scores.models import Score

User = get_user_model()


class Command(BaseCommand):
    help = "Set up demo data for the leaderboard system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=50,
            help="Number of demo users to create",
        )
        parser.add_argument(
            "--scores",
            type=int,
            default=500,
            help="Number of demo scores to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data first",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up demo data for leaderboard system..."))

        if options["clear"]:
            self.clear_demo_data()

        with transaction.atomic():
            # Create demo games
            games = self.create_demo_games()

            # Create demo users
            users = self.create_demo_users(options["users"])

            # Create demo scores
            self.create_demo_scores(games, users, options["scores"])

            # Show summary
            self.show_summary()

    def clear_demo_data(self):
        """Clear existing demo data."""
        self.stdout.write("Clearing existing demo data...")

        # Delete scores first due to foreign key constraints
        Score.objects.filter(user__email__contains="demo").delete()

        # Delete demo users
        User.objects.filter(email__contains="demo").delete()

        # Delete demo games
        Game.objects.filter(name__contains="Demo").delete()

        self.stdout.write(self.style.SUCCESS("Demo data cleared."))

    def create_demo_games(self):
        """Create demo games for testing."""
        self.stdout.write("Creating demo games...")

        games_data = [
            {
                "name": "Demo Racing Game",
                "description": "A fast-paced racing game where lower times are better",
                "score_type": "time",
                "is_active": True,
            },
            {
                "name": "Demo Shooting Game",
                "description": "An action-packed shooting game where higher scores are better",
                "score_type": "highest",
                "is_active": True,
            },
            {
                "name": "Demo Puzzle Game",
                "description": "A challenging puzzle game where lower move counts are better",
                "score_type": "lowest",
                "is_active": True,
            },
            {
                "name": "Demo Platform Game",
                "description": "A classic platformer where higher scores are better",
                "score_type": "highest",
                "is_active": True,
            },
            {
                "name": "Demo Strategy Game",
                "description": "A strategic game where higher scores represent better performance",
                "score_type": "highest",
                "is_active": True,
            },
        ]

        games = []
        for game_data in games_data:
            game, created = Game.objects.get_or_create(
                name=game_data["name"],
                defaults=game_data,
            )
            games.append(game)
            if created:
                self.stdout.write(f"  Created: {game.name}")
            else:
                self.stdout.write(f"  Exists: {game.name}")

        return games

    def create_demo_users(self, count):
        """Create demo users."""
        self.stdout.write(f"Creating {count} demo users...")

        users = []
        for i in range(1, count + 1):
            email = f"demo_user_{i}@example.com"
            name = f"Demo User {i}"

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "is_active": True,
                },
            )

            if created:
                user.set_password("demopass123")
                user.save()

            users.append(user)

        self.stdout.write(f"  Created/found {len(users)} demo users")
        return users

    def create_demo_scores(self, games, users, count):
        """Create demo scores."""
        self.stdout.write(f"Creating {count} demo scores...")

        scores_created = 0

        for _ in range(count):
            user = random.choice(users)
            game = random.choice(games)

            # Generate appropriate score based on game type
            if game.score_type == "highest":
                # Higher scores (0-10000)
                score = Decimal(str(random.randint(100, 10000)))
            elif game.score_type == "lowest":
                # Lower scores (1-100)
                score = Decimal(str(random.randint(1, 100)))
            else:  # time
                # Time in seconds with decimals (10-300 seconds)
                score = Decimal(str(round(random.uniform(10.0, 300.0), 2)))

            # Generate metadata
            metadata = {
                "level": random.randint(1, 10),
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "session_id": f"session_{random.randint(1000, 9999)}",
            }

            # Create score
            Score.objects.create(
                user=user,
                game=game,
                score=score,
                metadata=metadata,
            )

            scores_created += 1

            if scores_created % 50 == 0:
                self.stdout.write(f"  Created {scores_created} scores...")

        self.stdout.write(f"  Created {scores_created} demo scores")

    def show_summary(self):
        """Show summary of created data."""
        self.stdout.write(self.style.SUCCESS("\n" + "="*50))
        self.stdout.write(self.style.SUCCESS("DEMO DATA SETUP COMPLETE"))
        self.stdout.write(self.style.SUCCESS("="*50))

        # Games summary
        games_count = Game.objects.count()
        self.stdout.write(f"Total Games: {games_count}")

        # Users summary
        users_count = User.objects.count()
        demo_users_count = User.objects.filter(email__contains="demo").count()
        self.stdout.write(f"Total Users: {users_count} (including {demo_users_count} demo users)")

        # Scores summary
        scores_count = Score.objects.count()
        demo_scores_count = Score.objects.filter(user__email__contains="demo").count()
        self.stdout.write(f"Total Scores: {scores_count} (including {demo_scores_count} demo scores)")

        # Per-game summary
        self.stdout.write("\nScores per game:")
        for game in Game.objects.all():
            game_scores = Score.objects.filter(game=game).count()
            self.stdout.write(f"  {game.name}: {game_scores} scores")

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("You can now test the leaderboard API endpoints!"))
        self.stdout.write(self.style.SUCCESS("API Documentation: http://localhost:8000/api/docs/"))
        self.stdout.write("="*50)
