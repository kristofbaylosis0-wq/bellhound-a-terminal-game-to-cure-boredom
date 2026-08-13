from __future__ import annotations

import json
from pathlib import Path


CHAPTER = Path(__file__).parents[1] / "story" / "chapters" / "chapter_01.json"


def test_chapter_one_has_core_region_content() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    beats = data["beats"]
    ids = {beat["id"] for beat in beats}
    titles = {beat.get("title") for beat in beats}

    assert len(beats) >= 25
    assert "Ashenfall at Dusk" in titles
    assert "The Seventh Silence" in titles
    assert "The First Echo" in titles
    assert "The Hollow Bellkeeper" in titles
    assert "Chapter One — Complete" in titles
    assert "ch1_arrival" in ids
    assert "ch1_checkpoint" in ids

    assert data.get("mode") == "handcrafted"
    assert data.get("ai_required") is False
