"""Category registry for English learning courses.

Provides a centralized mapping of category slugs to display names,
matching the Engoo Daily News category tree.
"""

from pathlib import Path

# Engoo Daily News categories (slug → display name)
CATEGORY_TREE: dict[str, str] = {
    "business-politics": "Business & Politics",
    "culture-society": "Culture & Society",
    "health-lifestyle": "Health & Lifestyle",
    "science-technology": "Science & Technology",
    "travel-experiences": "Travel & Experiences",
}


def resolve_category(slug: str) -> str:
    """Convert a category slug to its display name.

    Returns the slug unchanged if not found in the tree.
    Returns empty string if slug is empty.
    """
    if not slug:
        return ""
    return CATEGORY_TREE.get(slug, slug)


def list_categories() -> list[tuple[str, str]]:
    """Return all categories as (slug, display_name) tuples."""
    return list(CATEGORY_TREE.items())


def auto_detect_category(directory: Path) -> str | None:
    """Try to match a directory name to a category slug.

    Checks exact match first. Returns the slug if found, None otherwise.
    """
    name = directory.name
    if name in CATEGORY_TREE:
        return name
    return None
