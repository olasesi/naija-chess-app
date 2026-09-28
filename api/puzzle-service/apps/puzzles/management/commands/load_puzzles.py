import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.puzzles.models import Puzzle


class Command(BaseCommand):
    help = "Load puzzles from a JSON data file into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to puzzles JSON (defaults to bundled data/puzzles.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing puzzles before loading",
        )

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parent.parent
        data_file = Path(options["file"]) if options["file"] else base / "data" / "puzzles.json"

        if not data_file.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {data_file}"))
            return

        with open(data_file, "r", encoding="utf-8") as f:
            puzzles_data = json.load(f)

        if options["clear"]:
            count, _ = Puzzle.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing puzzles"))

        created = 0
        skipped = 0

        with transaction.atomic():
            for entry in puzzles_data:
                fen = entry["fen"]
                exists = Puzzle.objects.filter(fen=fen, title=entry.get("title", "")).exists()
                if exists:
                    skipped += 1
                    continue

                Puzzle.objects.create(
                    fen=fen,
                    solution=entry["solution"],
                    rating=entry["rating"],
                    difficulty=entry.get("difficulty", "MEDIUM"),
                    themes=entry.get("themes", []),
                    title=entry.get("title", ""),
                    source=entry.get("source", "seed"),
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {created} puzzles ({skipped} skipped, {len(puzzles_data)} total in file)"
            )
        )
