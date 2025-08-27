import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.models import Brand, Agency, Ad, Tag
from core.utils import extract_youtube_id


class Command(BaseCommand):
    help = "Import Ads from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Validate without writing to DB",
        )
        parser.add_argument(
            "--append-tags", action="store_true",
            help="Append tags from CSV instead of replacing existing tags on the Ad",
        )

    def handle(self, *args, **options):
        path = Path(options["csv_path"]).expanduser()
        if not path.exists():
            raise CommandError(f"CSV not found: {path}")

        created = updated = skipped = 0

        # --- Read & normalise CSV headers/rows (robust to BOM & blank headers)
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            raw_fields = reader.fieldnames or []
            norm_fields = [(c or "").strip().lower() for c in raw_fields]
            keymap = {orig: norm for orig, norm in zip(raw_fields, norm_fields)}

            required = {"title", "brand", "youtube"}
            missing = required - set(norm_fields)
            if missing:
                raise CommandError(f"CSV missing required columns: {', '.join(sorted(missing))}")

            rows = []
            for raw in reader:
                row = {}
                for k, v in raw.items():
                    norm = keymap.get(k, "").strip().lower()
                    if not norm:
                        continue
                    row[norm] = (v or "").strip()
                rows.append(row)

        def _split_tags(tags_str: str) -> list[str]:
            if not tags_str:
                return []
            # split on commas, ignore empties, de-dup while preserving order
            seen, out = set(), []
            for piece in tags_str.split(","):
                name = piece.strip()
                if not name:
                    continue
                if name.lower() in seen:
                    continue
                seen.add(name.lower())
                out.append(name)
            return out

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
                tags_str = val("tags")  # ← CSV column for tags
                tag_names = _split_tags(tags_str)

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
                    defaults={"slug": slugify(brand_name)},
                )
                agency = None
                if agency_name:
                    agency, _ = Agency.objects.get_or_create(
                        name=agency_name,
                        defaults={"slug": slugify(agency_name)},
                    )

                defaults = {
                    "title": title,
                    "brand": brand,
                    "agency": agency,
                    "year": int(year) if year.isdigit() else None,
                    "duration_sec": int(duration) if duration.isdigit() else None,
                    "tags": tags_str,  # keep your legacy CharField if you still have it; harmless otherwise
                    "youtube_url": youtube,
                }

                ad, was_created = Ad.objects.update_or_create(
                    youtube_id=yt_id, defaults=defaults
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

                # --- Tags (M2M) ---
                if tag_names:
                    if not options.get("append-tags"):
                        ad.tags.clear()  # replace mode (default)
                    for name in tag_names:
                        tag, _ = Tag.objects.get_or_create(
                            slug=slugify(name),
                            defaults={"name": name},
                        )
                        ad.tags_m2m.add(tag)

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