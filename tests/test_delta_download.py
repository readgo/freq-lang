"""Test download_engoo_news.py delta logic:

- already-published articles (in manifest) are skipped → no re-generation
- new articles are packed and recorded in manifest only on success
- failed freqgen → not recorded → retried next run
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SPEC_PATH = Path(__file__).resolve().parent.parent / ".github/scripts/download_engoo_news.py"


@pytest.fixture
def denv(tmp_path, monkeypatch):
    """Load download_engoo_news.py as a module with mocks."""
    spec = importlib.util.spec_from_file_location("den", SPEC_PATH)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    monkeypatch.setattr(mod, "ARTICLES_DIR", tmp_path / "articles")
    monkeypatch.setattr(mod, "PACKS_DIR", tmp_path / "packs")
    monkeypatch.setattr(mod, "MANIFEST_FILE", tmp_path / "manifest.json")
    monkeypatch.setattr(mod, "download_manifest_from_release", lambda: True)
    monkeypatch.setattr(mod, "verify_ids", lambda: None)

    state = {"articles": [], "details": {}, "freqgen_ok": True, "freqgen_calls": []}

    # 只对第一个分类返回文章（真实脚本按 course_id 拉取各自分类的文章）
    _served = []

    def fake_get_articles(course_id, limit=10):
        if not _served:
            _served.append(course_id)
            return [{"lesson_id": a["id"], "title": a["title"]} for a in state["articles"]]
        return []

    def fake_get_detail(lesson_id):
        d = state["details"][lesson_id]
        return {"title": d["title"], "date": d["date"], "paragraphs": ["para one", "para two"]}

    def fake_run_freqgen(txt, pack_path, course_slug=None):
        state["freqgen_calls"].append((Path(txt).name, pack_path.name, course_slug))
        if state["freqgen_ok"]:
            pack_path.parent.mkdir(parents=True, exist_ok=True)
            pack_path.write_bytes(b"fakepack")
            return True
        return False

    monkeypatch.setattr(mod, "get_articles_by_course", fake_get_articles)
    monkeypatch.setattr(mod, "get_article_detail", fake_get_detail)
    monkeypatch.setattr(mod, "run_freqgen", fake_run_freqgen)

    return mod, state


def _run(mod, *extra):
    sys.argv = ["download_engoo_news.py", "--skip-verify", "--limit", "10", *extra]
    mod.main()


def _manifest(mod):
    return json.loads(mod.MANIFEST_FILE.read_text())


def _add_article(state, aid, title, date_str):
    state["articles"].append({"id": aid, "title": title})
    state["details"][aid] = {"title": title, "date": date_str}


def test_delta_skips_published_articles(denv):
    mod, state = denv
    # manifest already contains one article (第一个分类 slug 是 business-politics)
    mod.MANIFEST_FILE.write_text(
        json.dumps([["business-politics", "2026-08-01T17:00:00Z", "Old Article"]]),
        encoding="utf-8",
    )
    _add_article(state, "A1", "Old Article", "2026-08-01T17:00:00Z")
    _add_article(state, "A2", "New Article", "2026-08-02T17:00:00Z")

    _run(mod)

    # only the new article got packed
    names = [c[1] for c in state["freqgen_calls"]]
    assert names == ["day-20260802-new-article.freqpack"], names
    # manifest now has both
    assert len(_manifest(mod)) == 2


def test_failed_freqgen_not_recorded(denv):
    mod, state = denv
    _add_article(state, "A1", "Broken Article", "2026-08-02T17:00:00Z")
    state["freqgen_ok"] = False

    _run(mod)

    # pack failed → not added to manifest
    assert _manifest(mod) == []
    assert state["freqgen_calls"]  # freqgen was attempted


def test_rebuild_regenerates_all(denv):
    mod, state = denv
    mod.MANIFEST_FILE.write_text(
        json.dumps([["business-politics", "2026-08-01T17:00:00Z", "Old Article"]]),
        encoding="utf-8",
    )
    _add_article(state, "A1", "Old Article", "2026-08-01T17:00:00Z")
    _add_article(state, "A2", "New Article", "2026-08-02T17:00:00Z")

    _run(mod, "--rebuild")

    # both packed in rebuild mode
    names = sorted(c[1] for c in state["freqgen_calls"])
    assert names == [
        "day-20260801-old-article.freqpack",
        "day-20260802-new-article.freqpack",
    ], names
    assert len(_manifest(mod)) == 2
