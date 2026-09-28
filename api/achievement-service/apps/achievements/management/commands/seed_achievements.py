import json

from django.core.management.base import BaseCommand
from django.db import transaction

from achievements.models import Achievement


class Command(BaseCommand):
    help = "Seed the achievement catalog from the bundled JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete all achievements first")

    def handle(self, *args, **options):
        from pathlib import Path

        data_file = Path(__file__).resolve().parent.parent.parent / "data" / "achievements.json"
        if not data_file.exists():
            self.stderr.write(self.style.ERROR(f"Missing data file: {data_file}"))
            return

        with open(data_file, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        if options["clear"]:
            deleted, _ = Achievement.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing achievements"))

        created = updated = 0
        with transaction.atomic():
            for entry in catalog:
                obj, was_created = Achievement.objects.update_or_create(
                    code=entry["code"],
                    defaults={
                        "name": entry["name"],
                        "description": entry["description"],
                        "category": entry.get("category", "game"),
                        "icon": entry.get("icon", "🏆"),
                        "xp_reward": entry.get("xp_reward", 0),
                        "criteria": entry["criteria"],
                        "is_active": entry.get("is_active", True),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created} achievements, updated {updated}.")
        )