import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Brand, Agency, Ad
from core.utils import extract_youtube_id

class Command(BaseCommand):
    help = "Import Ads from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")

    def handle(self, *args, **options):
        path = Path(options["csv_path"]).expanduser()
        if not path.exists():
            raise CommandError(f"CSV not found: {path}")

        created = updated = skipped = 0

        # Open with utf-8-sig to strip BOM if present
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)

            raw_fields = reader.fieldnames or []
            norm_fields = [(c or "").strip().lower() for c in raw_fields]
            keymap = {orig: norm for orig, norm in zip(raw_fields, norm_fields)}

            required_cols = {"title", "brand", "youtube"}
            missing = required_cols - set(norm_fields)
            if missing:
                raise CommandError(f"CSV missing required columns: {', '.join(sorted(missing))}")

            rows = []
            for raw in reader:
                row = {}
                for k, v in raw.items():
                    norm = keymap.get(k, "").strip().lower()
                    if not norm:
                        continue  # skip columns with empty/None header
                    row[norm] = (v or "").strip()
                rows.append(row)

        @transaction.atomic
        def _run():
            nonlocal created, updated, skipped
            for i, row in enumerate(rows, start=2):  # header is line 1
                def val(*names):
                    for n in names:
                        x = row.get(n)
                        if x:
                            return x
                    return ""

                title = val("title")
                brand_name = val("brand")
                agency_name = val("agency") or None
                youtube = val("youtube", "youtube_url", "url", "video", "link")
                year = val("year")
                duration = val("duration_sec", "duration")
                tags = val("tags")

                if not title or not brand_name or not youtube:
                    self.stderr.write(f"[line {i}] missing title/brand/youtube → skipped")
                    skipped += 1
                    continue

                yt_id = extract_youtube_id(youtube)
                if not yt_id:
                    self.stderr.write(f"[line {i}] invalid YouTube URL/ID: {youtube} → skipped")
                    skipped += 1
                    continue

                brand, _ = Brand.objects.get_or_create(
                    name=brand_name,
                    defaults={"slug": brand_name.lower().replace(" ", "-")},
                )
                agency = None
                if agency_name:
                    agency, _ = Agency.objects.get_or_create(
                        name=agency_name,
                        defaults={"slug": agency_name.lower().replace(" ", "-")},
                    )

                defaults = {
                    "title": title,
                    "brand": brand,
                    "agency": agency,
                    "year": int(year) if year.isdigit() else None,
                    "duration_sec": int(duration) if duration.isdigit() else None,
                    "tags": tags,
                    "youtube_url": youtube,
                }

                ad, was_created = Ad.objects.update_or_create(
                    youtube_id=yt_id, defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        if options.get("dry_run"):
            try:
                with transaction.atomic():
                    _run()
                    raise RuntimeError("Dry run — rolling back")
            except RuntimeError:
                pass
        else:
            _run()

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))