from django.core.management.base import BaseCommand
from tournaments.models import Tournament, TournamentPlayer


class Command(BaseCommand):
    help = "Create a test tournament with sample players"

    def add_arguments(self, parser):
        parser.add_argument("--name", default="Test Tournament", type=str)
        parser.add_argument("--type", default="SWISS", choices=["SWISS", "ROUND_ROBIN"])
        parser.add_argument("--players", default=8, type=int)
        parser.add_argument("--rounds", default=5, type=int)

    def handle(self, *args, **options):
        t = Tournament.objects.create(
            name=options["name"],
            type=options["type"],
            total_rounds=options["rounds"],
            min_players=2,
            max_players=options["players"],
            creator_id="test-admin",
        )
        for i in range(options["players"]):
            TournamentPlayer.objects.create(
                tournament=t,
                user_id=f"test-player-{i + 1}",
                seed=i + 1,
            )
        self.stdout.write(self.style.SUCCESS(f"Created tournament {t.id} with {options['players']} players"))
