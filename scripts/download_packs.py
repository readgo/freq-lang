#!/usr/bin/env python3
"""
Download latest .freqpack files from GitHub Actions artifacts.

Usage:
    python scripts/download_packs.py
    python scripts/download_packs.py --run-id 123456789  # specific run
    python scripts/download_packs.py --token ghp_xxx     # use specific token
"""

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_DIR = Path(__file__).resolve().parent.parent
PACKS_DIR = BASE_DIR / "engoo_news"
STATE_FILE = PACKS_DIR / ".last_downloaded_run.json"

GH_API = "https://api.github.com"
REPO = "readgo/freq-lang"


def get_headers(args):
    """Build request headers with auth if available."""
    headers = {"Accept": "application/vnd.github+json"}
    token = args.token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        # Try to get from gh CLI if installed
        try:
            import subprocess
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                headers["Authorization"] = f"Bearer {result.stdout.strip()}"
        except FileNotFoundError:
            pass
    return headers


def api_get(path, headers):
    """Make a GET request to GitHub API."""
    url = f"{GH_API}{path}"
    req = Request(url, headers=headers)
    try:
        resp = urlopen(req)
        return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  ✗ API error {e.code}: {body}", file=sys.stderr)
        if e.code == 401:
            print("  Set GITHUB_TOKEN env var or use --token", file=sys.stderr)
        sys.exit(1)


def get_latest_successful_run(headers, branch="main"):
    """Get the latest successful workflow run ID."""
    workflows = api_get(f"/repos/{REPO}/actions/workflows", headers)
    workflow_id = None
    for w in workflows.get("workflows", []):
        if w.get("name") == "Engoo Daily News":
            workflow_id = w["id"]
            break
    if not workflow_id:
        print("  ✗ Workflow 'Engoo Daily News' not found", file=sys.stderr)
        sys.exit(1)

    # Get the latest successful run on the default branch
    runs = api_get(
        f"/repos/{REPO}/actions/workflows/{workflow_id}/runs"
        f"?branch={branch}&status=success&per_page=5",
        headers
    )
    run = None
    for r in runs.get("workflow_runs", []):
        if r.get("conclusion") == "success":
            run = r
            break

    if not run:
        print("  ✗ No successful runs found", file=sys.stderr)
        sys.exit(1)

    return run


def get_artifacts(run_id, headers):
    """Get artifacts for a specific run."""
    data = api_get(f"/repos/{REPO}/actions/runs/{run_id}/artifacts", headers)
    return data.get("artifacts", [])


def download_artifact(artifact_id, name, headers, dest):
    """Download and extract a zip artifact."""
    url = f"{GH_API}/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
    req = Request(url, headers=headers)
    # GitHub redirects to a signed download URL
    resp = urlopen(req)
    zip_path = dest / f"{name}.zip"
    with open(zip_path, "wb") as f:
        f.write(resp.read())

    # Extract
    extracted = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith(".freqpack"):
                target = dest / Path(member).name
                # Check if same file already exists
                if target.exists() and target.stat().st_size == zf.getinfo(member).file_size:
                    continue
                zf.extract(member, dest)
                # Move to flat dir
                src = dest / member
                if src != target:
                    src.rename(target)
                extracted += 1

    zip_path.unlink()  # remove zip after extraction

    # Clean up empty subdirectories
    for subdir in sorted(dest.iterdir(), reverse=True):
        if subdir.is_dir() and not any(subdir.iterdir()):
            subdir.rmdir()

    return extracted


def save_state(run_id):
    """Save the last downloaded run ID."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"run_id": run_id, "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, f)


def load_state():
    """Load the last downloaded run ID."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"run_id": 0}


def main():
    parser = argparse.ArgumentParser(description="Download .freqpack from GitHub Actions")
    parser.add_argument("--run-id", type=int, help="Specific run ID (default: latest)")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--force", action="store_true", help="Download even if already downloaded")
    args = parser.parse_args()

    headers = get_headers(args)
    if not headers.get("Authorization"):
        print("⚠ No GitHub token found. Trying unauthenticated (may hit rate limits)...")

    PACKS_DIR.mkdir(parents=True, exist_ok=True)

    if args.run_id:
        run_id = args.run_id
        print(f"Downloading artifacts from run #{run_id}...")
    else:
        state = load_state()
        run = get_latest_successful_run(headers)
        run_id = run["id"]
        run_created = run["created_at"][:19].replace("T", " ")

        if run_id == state.get("run_id") and not args.force:
            print(f"Already downloaded run #{run_id} ({run_created})")
            print("Use --force to download again")
            return

        print(f"Latest successful run: #{run_id} ({run_created})")

    artifacts = get_artifacts(run_id, headers)
    engoo_artifacts = [a for a in artifacts if a["name"].startswith("engoo-news")]

    if not engoo_artifacts:
        print("No engoo-news artifacts found in this run")
        sys.exit(1)

    total = 0
    for artifact in engoo_artifacts:
        print(f"  Downloading: {artifact['name']} ({artifact['size_in_bytes'] / 1024:.0f} KB)")
        count = download_artifact(artifact["id"], artifact["name"], headers, PACKS_DIR)
        total += count
        print(f"    → {count} pack(s) extracted")

    if not args.run_id:
        save_state(run_id)

    print(f"\nDone: {total} pack(s) in {PACKS_DIR}/")
    if total > 0:
        print("Run freqgen download script to see what's new:")
        print(f"  ls {PACKS_DIR}/{'cat/'}")


if __name__ == "__main__":
    main()
