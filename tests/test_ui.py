from __future__ import annotations

from game import ui


def test_menu_keeps_story_context_visible(monkeypatch, capsys) -> None:
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "read_key", lambda: "1")

    selected = ui.menu(
        "WHAT DO YOU DO?",
        ["Speak to Mira", "Inspect the bell"],
        context=["Mira Is Afraid", "'Do not answer anyone who calls your name.'", "The seventh bell hangs above you."],
    )

    assert selected == 0
    output = capsys.readouterr().out
    assert "Mira Is Afraid" in output
    assert "Do not answer anyone" in output
    assert "The seventh bell hangs above you." in output
    assert "Speak to Mira" in output
    assert "Inspect the bell" in output
