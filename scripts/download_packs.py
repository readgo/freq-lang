#!/usr/bin/env python3
"""
Download latest .freqpack Release from GitHub (public repo, no token needed).

Extracts to:
  EngooNews/
    ├── business-politics/day-20260705-xxx.freqpack
    └── science-technology/day-20260704-xxx.freqpack

Usage:
    python scripts/download_packs.py                  # latest release
    python scripts/download_packs.py --tag packs-20260707
    python scripts/download_packs.py --list
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_DIR = Path(__file__).resolve().parent.parent
PACKS_DIR = BASE_DIR / "EngooNews"

GH_API = "https://api.github.com"
REPO = "readgo/freq-lang"


def api_get(url):
    req = Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        return json.loads(urlopen(req).read())
    except HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        sys.exit(1)


def list_releases(limit=5):
    data = api_get(f"{GH_API}/repos/{REPO}/releases?per_page={limit}")
    for r in data:
        print(f"  {r['tag_name']}  ({r['created_at'][:10]})  {len(r.get('assets', []))} asset(s)")


def get_latest_release():
    return api_get(f"{GH_API}/repos/{REPO}/releases/latest")


def get_release_by_tag(tag):
    return api_get(f"{GH_API}/repos/{REPO}/releases/tags/{tag}")


def download_and_extract(asset, dest):
    zip_url = asset["browser_download_url"]
    name = asset["name"].replace(".zip", "")
    req = Request(zip_url)
    resp = urlopen(req)
    zip_path = dest / f"{name}.zip"
    with open(zip_path, "wb") as f:
        f.write(resp.read())

    extracted = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if not member.endswith(".freqpack"):
                continue
            # Zip structure: EngooNews/business-politics/day-xxx.freqpack
            # Strip the top-level directory to get: business-politics/day-xxx.freqpack
            parts = Path(member).parts
            rel_path = Path(*parts[1:]) if len(parts) >= 2 else Path(member).name
            target = dest / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.stat().st_size == zf.getinfo(member).file_size:
                continue
            # Extract directly to target, not to nested path
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted += 1
    zip_path.unlink()
    return extracted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Release tag (default: latest)")
    parser.add_argument("--list", action="store_true", help="List recent releases")
    args = parser.parse_args()

    if args.list:
        print("Recent releases:")
        list_releases()
        return

    PACKS_DIR.mkdir(parents=True, exist_ok=True)

    if args.tag:
        print(f"Fetching release: {args.tag}")
        release = get_release_by_tag(args.tag)
    else:
        release = get_latest_release()

    tag = release["tag_name"]
    assets = release.get("assets", [])

    if not assets:
        print(f"No assets in release {tag}")
        sys.exit(1)

    total = 0
    for asset in assets:
        name = asset["name"]
        if not name.endswith(".zip"):
            continue
        size_kb = asset["size"] / 1024
        print(f"  Download: {name} ({size_kb:.0f} KB)")
        count = download_and_extract(asset, PACKS_DIR)
        total += count

    print(f"\nDone: {total} pack(s) → {PACKS_DIR}/")


if __name__ == "__main__":
    main()
