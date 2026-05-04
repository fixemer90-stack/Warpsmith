"""Tests for F4.8 — SVG Icons Integration."""

import pytest

from backend.loader.icon_map import (
    CATEGORY_COLORS,
    ICON_MAP,
    get_card_style,
    get_icon_html,
    get_icon_svg_map,
    get_icon_url,
)


class TestIconRegistry:
    def test_all_categories_in_icon_map(self):
        """All 18 categories are in ICON_MAP."""
        assert len(ICON_MAP) == 18

    def test_icon_html_returns_svg(self):
        """get_icon_html returns valid SVG."""
        html = get_icon_html("character")
        assert "<svg" in html
        assert 'width="24"' in html

    def test_icon_html_fallback(self):
        """get_icon_html returns infantry fallback for unknown category."""
        html = get_icon_html("nonexistent")
        assert "<!-- icon" in html or "<svg" in html

    def test_card_style_returns_css(self):
        """get_card_style returns correct CSS."""
        style = get_card_style("character")
        assert style.startswith("border-left:")
        assert CATEGORY_COLORS["character"] in style

    def test_card_style_fallback(self):
        """get_card_style returns default color for unknown category."""
        style = get_card_style("unknown")
        assert "#6b7280" in style

    def test_all_svg_files_exist(self):
        """All 18 SVG icon files exist on disk."""
        from pathlib import Path

        icons_dir = Path(__file__).parent.parent / "web" / "static" / "icons"
        missing = []
        for filename in ICON_MAP.values():
            path = icons_dir / filename
            if not path.exists():
                missing.append(filename)
        assert not missing, f"Missing SVG files: {missing}"

    def test_get_icon_url(self):
        """get_icon_url returns correct URL."""
        url = get_icon_url("battleline")
        assert url == "/static/icons/battleline.svg"

    def test_get_icon_url_fallback(self):
        """get_icon_url falls back to infantry.svg."""
        url = get_icon_url("nonexistent")
        assert "infantry.svg" in url

    def test_get_icon_svg_map_all_categories(self):
        """get_icon_svg_map returns all 18 categories."""
        svg_map = get_icon_svg_map()
        for cat in ICON_MAP:
            assert cat in svg_map, f"Missing category: {cat}"

    def test_icon_html_inline_size(self):
        """get_icon_html respects custom size."""
        html = get_icon_html("character", size=48)
        assert 'width="48"' in html
        assert 'height="48"' in html
