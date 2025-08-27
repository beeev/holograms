# core/management/commands/import_ads_csv.py
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from core.models import Ad, Brand, Agency, Tag
from core.utils import extract_youtube_id


class Command(BaseCommand):
    help = "Import ads from a CSV. Columns: title,brand,agency,year,youtube,duration_sec,tags"

    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=str, help="Path to CSV file")
        parser.add_argument("--dry-run", action="store_true",
                            help="Print what would happen; do not write to DB")
        parser.add_argument("--append-tags", action="store_true",
                            help="Append tags instead of replacing existing ones")

    # ---- helpers -------------------------------------------------------------

    def _detect_dialect(self, sample: str):
        """Return a csv.Dialect for comma or semicolon; fall back to comma."""
        try:
            return csv.Sniffer().sniff(sample, delimiters=";,")
        except csv.Error:
            class _Fallback(csv.Dialect):
                delimiter = ","
                quotechar = '"'
                doublequote = True
                skipinitialspace = False
                lineterminator = "\n"
                quoting = csv.QUOTE_MINIMAL
            return _Fallback()

    def _split_tags(self, tags_str: str):
        seen, out = set(), []
        for piece in (tags_str or "").split(","):
            name = piece.strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(name)
        return out

    # ---- main ---------------------------------------------------------------

    def handle(self, *args, **opts):
        path = Path(opts["csvfile"]).expanduser()
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        # Read file with BOM handling and delimiter sniffing
        with path.open(encoding="utf-8-sig", newline="") as f:
            sample = f.read(2048)
            f.seek(0)
            dialect = self._detect_dialect(sample)
            reader = csv.DictReader(f, dialect=dialect)

            fields = [ (c or "").strip().lower() for c in (reader.fieldnames or []) ]
            required = {"title", "brand", "youtube"}
            missing = required - set(fields)
            if missing:
                raise CommandError(f"CSV missing required columns: {', '.join(sorted(missing))}")

            rows = list(reader)

        self.stdout.write(f"Loaded {len(rows)} rows from {path}")
        self.stdout.write(f"Detected delimiter: {repr(getattr(dialect, 'delimiter', ','))}")

        created, updated, skipped = 0, 0, 0
        dry = opts["dry_run"]
        append_tags = opts["append_tags"]

        for i, raw in enumerate(rows, start=2):  # header is line 1
            # Normalise keys -> lower/stripped
            row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }

            title = row.get("title")
            brand_name = row.get("brand")
            agency_name = row.get("agency") or ""
            year_str = row.get("year") or ""
            youtube_in = row.get("youtube")
            duration_str = row.get("duration_sec") or ""
            tags_str = row.get("tags") or ""

            if not title or not brand_name or not youtube_in:
                self.stderr.write(f"[line {i}] missing title/brand/youtube → skipped")
                skipped += 1
                continue

            yt_id = extract_youtube_id(youtube_in)
            if not yt_id:
                self.stderr.write(f"[line {i}] invalid YouTube URL/ID: {youtube_in} → skipped")
                skipped += 1
                continue

            # Look up Brand/Agency by NAME (unique), slug is just a default
            if dry:
                brand = Brand(name=brand_name)
                agency = Agency(name=agency_name) if agency_name else None
            else:
                brand, _ = Brand.objects.get_or_create(
                    name=brand_name, defaults={"slug": slugify(brand_name)}
                )
                agency = None
                if agency_name:
                    agency, _ = Agency.objects.get_or_create(
                        name=agency_name, defaults={"slug": slugify(agency_name)}
                    )

            # Prepare common fields
            year = int(year_str) if year_str.isdigit() else None
            duration = int(duration_str) if duration_str.isdigit() else None
            tags_list = self._split_tags(tags_str)

            # Upsert by youtube_id (natural key)
            if dry:
                # Simulate: check if an Ad *would* exist (best-effort)
                # In dry-run we can’t hit DB reliably without reading, but we can just print
                action = "CREATE or UPDATE"
                self.stdout.write(f"[line {i}] {action}: {title} (yt:{yt_id})")
            else:
                ad, was_created = Ad.objects.get_or_create(
                    youtube_id=yt_id,
                    defaults={
                        "title": title,
                        "brand": brand,
                        "agency": agency or None,
                        "year": year,
                        "duration_sec": duration,
                        # store canonical URL; model clean/save will ensure this too
                        "youtube_url": f"https://www.youtube.com/watch?v={yt_id}",
                        # keep raw CSV text if you still have CharField 'tags'
                        "tags": tags_str,
                    },
                )
                if not was_created:
                    # Update existing record
                    ad.title = title
                    ad.brand = brand
                    ad.agency = agency or None
                    ad.year = year
                    ad.duration_sec = duration
                    ad.youtube_url = f"https://www.youtube.com/watch?v={yt_id}"
                    ad.tags = tags_str
                    ad.save()
                    updated += 1
                    action = "UPDATED"
                else:
                    created += 1
                    action = "CREATED"

                # M2M tags (on your field 'tags_m2m')
                if not append_tags:
                    ad.tags_m2m.clear()
                for name in tags_list:
                    tag, _ = Tag.objects.get_or_create(
                        name=name, defaults={"slug": slugify(name)}
                    )
                    ad.tags_m2m.add(tag)

                self.stdout.write(f"[line {i}] {action}: {ad.title}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

        if dry:
            self.stdout.write(self.style.WARNING("Dry run: no database writes were made."))