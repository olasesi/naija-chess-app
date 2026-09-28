import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.puzzles.models import DailyPuzzle, Puzzle


class Command(BaseCommand):
    help = "Set the puzzle of the day for a given date (default: today)"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, default=None, help="Date in YYYY-MM-DD format")
        parser.add_argument("--difficulty", type=str, default=None, help="Filter by difficulty")

    def handle(self, *args, **options):
        if options["date"]:
            target_date = timezone.datetime.strptime(options["date"], "%Y-%m-%d").date()
        else:
            target_date = timezone.now().date()

        qs = Puzzle.objects.filter(status="ACTIVE")
        if options["difficulty"]:
            qs = qs.filter(difficulty=options["difficulty"].upper())

        if not qs.exists():
            self.stderr.write(self.style.ERROR("No puzzles available. Run load_puzzles first."))
            return

        # Avoid reusing yesterday's puzzle
        yesterday = DailyPuzzle.objects.filter(date=target_date - timezone.timedelta(days=1)).first()
        if yesterday:
            qs = qs.exclude(id=yesterday.puzzle_id)

        puzzle = random.choice(list(qs[:200])) if qs.count() > 200 else random.choice(list(qs))

        daily, created = DailyPuzzle.objects.update_or_create(
            date=target_date,
            defaults={"puzzle": puzzle},
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} daily puzzle for {target_date}: {puzzle.title or puzzle.id} "
                f"({puzzle.difficulty}, {puzzle.rating})"
            )
        )
