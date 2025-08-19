from pathlib import Path
import polib
from django.conf import settings
from django.core.management.base import BaseCommand
from catalog.models import Category

LANGS = ["ar", "de"]

class Command(BaseCommand):
    help = "Seed locale django.po with Category names (msgctxt='category name')."

    def handle(self, *args, **opts):
        names = list(Category.objects.values_list("name", flat=True).distinct())
        if not names:
            self.stdout.write("No categories found."); return

        po_dir = Path(settings.BASE_DIR) / "locale"
        for lang in LANGS:
            po_path = po_dir / lang / "LC_MESSAGES" / "django.po"
            if not po_path.exists():
                self.stderr.write(f"Missing {po_path}. Run makemessages first."); continue

            po = polib.pofile(str(po_path), encoding="utf-8")
            existing = {(e.msgctxt, e.msgid) for e in po if not e.obsolete}
            added = 0
            for name in names:
                if not name: continue
                key = ("category name", name)
                if key in existing: continue
                po.append(polib.POEntry(msgctxt="category name", msgid=name, msgstr="")); added += 1
            if added:
                po.save(str(po_path)); self.stdout.write(f"[{lang}] added {added} entries")
            else:
                self.stdout.write(f"[{lang}] no new entries")
