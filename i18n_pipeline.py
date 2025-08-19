# i18n_pipeline.py
from __future__ import annotations
import os, sys, subprocess, codecs
from pathlib import Path
from typing import Tuple, Dict, Any
import polib

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None  # fallback to glossary only

# ----- CONFIG -----
ROOT = Path(__file__).parent
MANAGE = ROOT / "manage.py"
LOCALE = ROOT / "locale"
LANGS = ["ar", "de"]               # extend if needed
EXTS = ["html", "txt", "py"]       # files scanned by makemessages

GLOSSARY: Dict[str, Dict[str, str]] = {
    "ar": {
        "All Products": "جميع المنتجات",
        "Products": "المنتجات",
        "Home": "الصفحة الرئيسية",
        "Shop Now": "تسوق الآن",
        "Search our site": "ابحث في الموقع",
        "My Account": "حسابي",
        "My Profile": "ملفي الشخصي",
        "Logout": "تسجيل الخروج",
        "Login": "تسجيل الدخول",
        "Register": "تسجيل",
        "Product Management": "إدارة المنتجات",
        "Start shopping here": "ابدأ التسوق من هنا",
        "Profile updated successfully": "تم تحديث الملف الشخصي بنجاح",
    },
    "de": {
        "All Products": "Alle Produkte",
        "Products": "Produkte",
        "Home": "Startseite",
        "Shop Now": "Jetzt einkaufen",
        "Search our site": "Unsere Seite durchsuchen",
        "My Account": "Mein Konto",
        "My Profile": "Mein Profil",
        "Logout": "Abmelden",
        "Login": "Anmelden",
        "Register": "Registrieren",
        "Product Management": "Produktmanagement",
        "Start shopping here": "Beginnen Sie hier mit dem Einkaufen",
        "Profile updated successfully": "Profil erfolgreich aktualisiert",
    },
}

# ----- UTIL -----
def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=False).returncode

def strip_bom_and_fix_header(po_path: Path) -> None:
    if not po_path.exists():
        return
    raw = codecs.open(po_path, "r", "utf-8-sig").read()
    i = raw.find('msgid ""')
    if i == -1:
        lang = po_path.parent.parent.name
        header = (
            'msgid ""\n'
            'msgstr ""\n'
            f'"Language: {lang}\\n"\n'
            '"MIME-Version: 1.0\\n"\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Content-Transfer-Encoding: 8bit\\n"\n'
        )
        cleaned = header + "\n"
    else:
        cleaned = raw[i:]
    po_path.write_text(cleaned, encoding="utf-8")

def ensure_headers(po: polib.POFile, lang: str) -> None:
    po.metadata["Language"] = lang
    po.metadata["MIME-Version"] = "1.0"
    po.metadata["Content-Type"] = "text/plain; charset=UTF-8"
    po.metadata["Content-Transfer-Encoding"] = "8bit"
    if lang == "ar":
        po.metadata["Plural-Forms"] = (
            "nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : "
            "n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5;"
        )
    elif lang == "de":
        po.metadata["Plural-Forms"] = "nplurals=2; plural=(n != 1);"

def dedupe_inplace(po: polib.POFile) -> int:
    seen: Dict[Tuple[str,str,str], polib.POEntry] = {}
    kept, removed = [], 0
    for e in list(po):
        if e.obsolete:
            kept.append(e); continue
        key = (e.msgctxt or "", e.msgid, e.msgid_plural or "")
        if key in seen:
            master = seen[key]
            # prefer populated translations
            if not master.msgid_plural:
                if not master.msgstr and e.msgstr:
                    master.msgstr = e.msgstr
            else:
                for k, v in e.msgstr_plural.items():
                    if v and not master.msgstr_plural.get(k):
                        master.msgstr_plural[int(k)] = v
            # merge meta
            master.occurrences = sorted(set(master.occurrences + e.occurrences))
            master.flags = sorted(set(master.flags) | set(e.flags))
            if e.tcomment:
                master.tcomment = (master.tcomment + "\n" + e.tcomment).strip() if master.tcomment else e.tcomment
            if e.comment:
                master.comment = (master.comment + "\n" + e.comment).strip() if master.comment else e.comment
            removed += 1
        else:
            seen[key] = e
            kept.append(e)
    po._entries = kept
    return removed

def fix_newline_parity(po: polib.POFile) -> int:
    changed = 0
    for e in po:
        if e.obsolete: continue
        id_nl = e.msgid.startswith("\n")
        if e.msgstr:
            if id_nl and not e.msgstr.startswith("\n"):
                e.msgstr = "\n" + e.msgstr; changed += 1
            if not id_nl and e.msgstr.startswith("\n"):
                e.msgstr = e.msgstr.lstrip("\n"); changed += 1
        if e.msgid_plural and e.msgstr_plural:
            for k, v in list(e.msgstr_plural.items()):
                if id_nl and not v.startswith("\n"):
                    e.msgstr_plural[int(k)] = "\n" + v; changed += 1
                if not id_nl and v.startswith("\n"):
                    e.msgstr_plural[int(k)] = v.lstrip("\n"); changed += 1
    return changed

# translation helpers
import re
PH_RE = re.compile(
    r"""
    %\([^)]+\)[#0\- +]?\d*(?:\.\d+)?[sdifuxXeEgGcr] |
    %\d*\$?[#0\- +]?\d*(?:\.\d+)?[sdifuxXeEgGcr]   |
    \{[^}]+\}
    """, re.VERBOSE,
)
def extract_placeholders(s: str):
    return [(m.start(), m.end(), m.group(0)) for m in PH_RE.finditer(s or "")]

def translate_chunk(text: str, lang: str) -> str:
    if not text or text.isspace(): return text or ""
    g = GLOSSARY.get(lang, {})
    if text in g: return g[text]
    if GoogleTranslator is None: return text
    try:
        out = GoogleTranslator(source="en", target=lang).translate(text)
        return out if isinstance(out, str) and out else text
    except Exception:
        return text

def segment_translate(s: str, lang: str) -> str:
    if not s: return ""
    phs = extract_placeholders(s)
    if not phs: return translate_chunk(s, lang)
    parts, last = [], 0
    for start, end, ph in phs:
        if start > last:
            parts.append(translate_chunk(s[last:start], lang))
        parts.append(ph); last = end
    if last < len(s): parts.append(translate_chunk(s[last:], lang))
    return "".join(parts)

def validate_placeholders(src: str, dst: str) -> str:
    from collections import Counter
    src_ph = [t for *_, t in extract_placeholders(src)]
    dst_ph = [t for *_, t in extract_placeholders(dst)]
    need, have = Counter(src_ph), Counter(dst_ph)
    missing = []
    for k, cnt in need.items():
        if have[k] < cnt: missing.extend([k]*(cnt-have[k]))
    return (dst.rstrip()+" "+ " ".join(missing)).strip() if missing else dst

# optional: seed Category names with msgctxt="category name"
def seed_category_names() -> None:
    try:
        import django
        if not os.environ.get("DJANGO_SETTINGS_MODULE"):
            # best guess; adjust if different
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
        django.setup()
        from catalog.models import Category
        names = list(Category.objects.values_list("name", flat=True).distinct())
    except Exception as e:
        print(f"seed: skipped ({e.__class__.__name__}: {e})")
        return

    for lang in LANGS:
        po_path = LOCALE / lang / "LC_MESSAGES" / "django.po"
        if not po_path.exists():
            continue
        po = polib.pofile(str(po_path), encoding="utf-8-sig")
        existing = {(e.msgctxt, e.msgid) for e in po if not e.obsolete}
        added = 0
        for name in names:
            key = ("category name", name)
            if name and key not in existing:
                po.append(polib.POEntry(msgctxt="category name", msgid=name, msgstr=""))
                added += 1
        if added:
            po.save(str(po_path))
            print(f"{lang}: seeded {added} category names")

def process_po_file(po_path: Path) -> None:
    strip_bom_and_fix_header(po_path)
    lang = po_path.parent.parent.name
    po = polib.pofile(str(po_path), encoding="utf-8")
    ensure_headers(po, lang)
    removed = dedupe_inplace(po)

    changed = 0
    for e in po:
        if e.obsolete: continue
        # translate if empty
        if e.msgid_plural:
            if not e.msgstr:
                s_tr = validate_placeholders(e.msgid, segment_translate(e.msgid, lang))
                if s_tr: e.msgstr = s_tr; changed += 1
            plural_tr = validate_placeholders(e.msgid_plural, segment_translate(e.msgid_plural, lang))
            if not e.msgstr_plural: e.msgstr_plural = {}
            plural_count = 6 if lang == "ar" else 2
            for i in range(plural_count):
                if not e.msgstr_plural.get(i):
                    e.msgstr_plural[i] = plural_tr; changed += 1
        else:
            if not e.msgstr:
                tr = validate_placeholders(e.msgid, segment_translate(e.msgid, lang))
                if tr and tr != e.msgid:
                    e.msgstr = tr; changed += 1
                elif e.msgid in GLOSSARY.get(lang, {}):
                    e.msgstr = GLOSSARY[lang][e.msgid]; changed += 1

        if "fuzzy" in e.flags and e.msgstr:
            e.flags = [f for f in e.flags if f != "fuzzy"]

    changed += fix_newline_parity(po)
    po.save(str(po_path))
    print(f"{po_path}: deduped={removed}, updated={changed}")

def makemessages() -> None:
    args = [sys.executable, str(MANAGE), "makemessages"]
    for l in LANGS: args += ["-l", l]
    args += ["-e", ",".join(EXTS)]
    code = run(args)
    if code != 0:
        print("makemessages failed; continuing with existing .po files")

def compilemessages() -> None:
    args = [sys.executable, str(MANAGE), "compilemessages"]
    for l in LANGS: args += ["-l", l]
    code = run(args)
    if code != 0:
        print("compilemessages reported errors")

def main() -> None:
    # 0) pre-clean headers + dedupe to avoid msgmerge errors
    for lang in LANGS:
        po_path = LOCALE / lang / "LC_MESSAGES" / "django.po"
        if po_path.exists():
            strip_bom_and_fix_header(po_path)
            po = polib.pofile(str(po_path), encoding="utf-8")
            ensure_headers(po, lang)
            removed = dedupe_inplace(po)
            po.save(str(po_path))
            print(f"{po_path}: pre-dedup removed={removed}")

    # 1) extract from code/templates
    makemessages()

    # 2) seed DB-driven category names (optional, skips if Django not configured)
    seed_category_names()

    # 3) translate + tidy per file
    for lang in LANGS:
        po_path = LOCALE / lang / "LC_MESSAGES" / "django.po"
        if po_path.exists():
            process_po_file(po_path)

    # 4) compile .mo
    compilemessages()
    print("i18n pipeline done.")

if __name__ == "__main__":
    main()
