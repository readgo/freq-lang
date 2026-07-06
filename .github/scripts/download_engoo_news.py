#!/usr/bin/env python3
"""
Engoo Daily News downloader + freqgen pack producer.

Pipeline:
  1. Fetch articles from Engoo API → download new .txt
  2. For each new .txt → freqgen → .freqpack

Output structure:
  engoo_articles/{category}/day-YYYYMMDD-{title}.txt
  engoo_news/{category}/day-YYYYMMDD-{title}.freqpack
  (no date subdirectories, date is part of filename)

Usage:
    python scripts/download_engoo_news.py                  # full run
    python scripts/download_engoo_news.py --dry-run         # preview
    python scripts/download_engoo_news.py --limit 5
    python scripts/download_engoo_news.py --category business
    python scripts/download_engoo_news.py --rebuild         # rebuild all packs
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = BASE_DIR / "engoo_articles"
PACKS_DIR = BASE_DIR / "engoo_news"
FREQGEN_CMD = "freqgen"
MANIFEST_FILE = BASE_DIR / "engoo_manifest.json"

API_BASE = "https://api.engoo.com/api"

IDS = {
    "brand": "5a4657f2-e151-4c48-9cce-000000000002",
    "org":   "5d2656f1-9162-461d-88c7-b2505623d8cb",
    "daily_news_cat": "0225ae09-5d63-41c2-bd75-693985d07d78",
    "courses": {
        "Business & Politics": "838db612-5db8-4f6f-9ca7-8643e42de879",
        "Science & Technology": "36c03b50-bbba-481f-a7e4-d2b29d3fa47c",
    },
}

COURSE_META = {
    "Business & Politics": {"key": "business", "slug": "business-politics"},
    "Science & Technology": {"key": "science", "slug": "science-technology"},
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
})


# ── helpers ────────────────────────────────────────────────────────────

def get_text(obj, field="text"):
    if isinstance(obj, dict):
        if field in obj and isinstance(obj[field], dict):
            return obj[field].get("text", "")
        return obj.get(field, "")
    return str(obj) if obj else ""


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:80]


def fmt_date(iso_str):
    """Convert ISO date to YYYYMMDD."""
    if not iso_str:
        return datetime.now().strftime("%Y%m%d")
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y%m%d")
    except (ValueError, AttributeError):
        return datetime.now().strftime("%Y%m%d")


def article_filename(title, date_str):
    """Generate filename: day-YYYYMMDD-title.txt"""
    d = fmt_date(date_str)
    s = slugify(title)
    return f"day-{d}-{s}.txt"


def pack_filename(title, date_str):
    """Generate filename: day-YYYYMMDD-title.freqpack"""
    d = fmt_date(date_str)
    s = slugify(title)
    return f"day-{d}-{s}.freqpack"


def content_hash(title, paragraphs):
    return hashlib.md5((title + "\n" + "\n".join(paragraphs)).encode("utf-8")).hexdigest()


# ── API ────────────────────────────────────────────────────────────────

def verify_ids():
    resp = session.get(f"{API_BASE}/brands", params={"domain": "engoo.com"})
    resp.raise_for_status()
    print(f"✓ Connected: {get_text(resp.json()['data'][0], 'name')}")
    resp = session.get(f"{API_BASE}/categories/{IDS['daily_news_cat']}")
    resp.raise_for_status()
    print(f"✓ Category: {resp.json()['data'].get('name_text',{}).get('text','?')}")
    for name, cid in IDS["courses"].items():
        r = session.get(f"{API_BASE}/courses/{cid}")
        if r.status_code == 200:
            print(f"✓ Course: {name}")
        else:
            print(f"⚠ Course '{name}' not found (IDs may have changed)")
    print()


def get_articles_by_course(course_id, limit=10):
    url = f"{API_BASE}/lesson_headers/by_course"
    params = {
        "category": IDS["daily_news_cat"], "count": limit,
        "for_brand": IDS["brand"], "published_latest": "true", "type": "Published",
    }
    resp = session.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    refs = data.get("references", {})
    articles = []
    for entry in data.get("data", []):
        course_ref = entry.get("course", {}).get("_ref", "")
        if refs.get(course_ref, {}).get("id") != course_id:
            continue
        for lref in entry.get("lessons", []):
            ld = refs.get(lref.get("_ref", ""), {})
            if ld.get("_type") != "LessonHeader":
                continue
            mid = ld.get("master_id", "")
            title = get_text(ld, "title_text")
            if mid and title:
                articles.append({"lesson_id": mid, "title": title})
    return articles


def get_article_detail(lesson_id):
    url = f"{API_BASE}/lessons/{lesson_id}/current"
    params = {
        "context_organization": IDS["org"],
        "include_canonical_contexts": "true",
        "include_conversation_counts": "false",
    }
    resp = session.get(url, params=params)
    resp.raise_for_status()
    d = resp.json().get("data", {})
    paragraphs = []
    for ex in d.get("exercises", []):
        for sec in ex.get("sections", []):
            if sec.get("_type") != "ArticleSection":
                continue
            for para in sec.get("paragraphs", []):
                if para.get("_type") != "Paragraph":
                    continue
                para_text = "".join(
                    get_text(s, "text")
                    for s in para.get("paragraph_sentences", [])
                    if s.get("_type") == "ParagraphSentence"
                )
                if para_text.strip():
                    paragraphs.append(para_text.strip())
    return {
        "title": get_text(d, "title_text"),
        "date": d.get("first_published_at", ""),
        "paragraphs": paragraphs,
    }


# ── file ops ───────────────────────────────────────────────────────────

def load_manifest():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return set(tuple(e) for e in json.load(f))
    return set()


def save_manifest(processed_set):
    data = sorted([list(e) for e in processed_set])
    with open(MANIFEST_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_processed(course_slug, title, date_str, manifest):
    key = (course_slug, date_str, title)
    return key in manifest


def save_article(course_slug, title, date_str, paragraphs):
    fname = article_filename(title, date_str)
    cat_dir = ARTICLES_DIR / course_slug
    cat_dir.mkdir(parents=True, exist_ok=True)
    path = cat_dir / fname
    with open(path, "w", encoding="utf-8") as f:
        f.write(title + "\n\n")
        for p in paragraphs:
            f.write(p + "\n\n")
    return path


def get_pack_path(course_slug, title, date_str):
    fname = pack_filename(title, date_str)
    cat_dir = PACKS_DIR / course_slug
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir / fname


def run_freqgen(txt_path, pack_path):
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FREQGEN_CMD, str(txt_path), "-o", str(pack_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"  ✓ {pack_path.name}")
        else:
            err = (result.stderr or result.stdout).strip()[:120]
            print(f"  ✗ freqgen: {err}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  ✗ freqgen timed out")
        return False
    except FileNotFoundError:
        print("  ✗ freqgen not installed. Run: pip install -e .")
        return False


# ── main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--category", default="all",
                        help="business, science, or all")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--skip-freqgen", action="store_true")
    parser.add_argument("--rebuild", action="store_true",
                        help="Rebuild packs even if .freqpack exists")
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args()

    if not args.skip_verify:
        verify_ids()

    courses = {}
    for name, cid in IDS["courses"].items():
        meta = COURSE_META.get(name)
        if meta:
            courses[meta["key"]] = {"id": cid, "name": name, "slug": meta["slug"]}

    cats = list(courses.keys())
    if args.category != "all":
        if args.category not in cats:
            sys.exit(f"Unknown. Available: {', '.join(cats)}")
        cats = [args.category]

    print(f"Articles → {ARTICLES_DIR}/{{cat}}/day-YYYYMMDD-title.txt")
    print(f"Packs    → {PACKS_DIR}/{{cat}}/day-YYYYMMDD-title.freqpack")
    if args.dry_run:
        print("Mode: DRY RUN\n")

    manifest = load_manifest()
    total_new = total_dupes = total_packs = total_skipped = 0

    for cat_key in cats:
        course = courses[cat_key]
        print(f"\n── {course['name']} ──")

        try:
            articles = get_articles_by_course(course["id"], limit=args.limit)
        except Exception as e:
            print(f"  ✗ {e}")
            continue

        print(f"  {len(articles)} article(s)")

        for art in articles:
            print(f"\n  ─ {art['title'][:70]}")

            try:
                detail = get_article_detail(art["lesson_id"])
            except Exception as e:
                print(f"    ✗ {e}")
                continue

            if not detail["paragraphs"]:
                print(f"    ⚠ no paragraphs")
                continue

            title = detail["title"]
            date_str = detail["date"]

            if is_processed(course["slug"], title, date_str, manifest):
                print(f"    → article exists")
                total_dupes += 1
            else:
                if args.dry_run:
                    print(f"    → article: {article_filename(title, date_str)}")
                else:
                    txt = save_article(course["slug"], title, date_str, detail["paragraphs"])
                    print(f"    → article: {txt.name}")
                total_new += 1

            # Mark as processed
            manifest.add((course["slug"], date_str, title))

            if args.skip_freqgen:
                continue

            pack_path = get_pack_path(course["slug"], title, date_str)

            if pack_path.exists() and not args.rebuild:
                print(f"    → pack exists: {pack_path.name}")
                total_skipped += 1
            else:
                if args.dry_run:
                    print(f"    → pack: {pack_path.name}")
                else:
                    ok = run_freqgen(txt, pack_path)
                    if ok:
                        total_packs += 1
                    time.sleep(0.3)

    # Save updated manifest
    save_manifest(manifest)

    # Cleanup: remove source txt files (intermediate, not tracked by git)
    for cat_dir in ARTICLES_DIR.iterdir():
        if cat_dir.is_dir():
            for f in cat_dir.glob("*.txt"):
                f.unlink()
            try:
                cat_dir.rmdir()
            except OSError:
                pass

    print(f"\n── Summary ──")
    print(f"  New articles: {total_new}")
    print(f"  Duplicates:   {total_dupes}")
    print(f"  Packs built:  {total_packs}")
    print(f"  Packs skipped:{total_skipped}")
    if not args.skip_freqgen:
        print(f"  Packs → {PACKS_DIR}/{{cat}}/")


if __name__ == "__main__":
    main()
