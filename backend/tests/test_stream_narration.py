"""CR12: streamed narration must never leak the [Narration]/[StateUpdates] tags,
even when a tag is split across chunks."""

from backend.engine import stream_narration


def _join(chunks):
    return "".join(stream_narration(iter(chunks)))


def test_strips_narration_header_and_stops_at_stateupdates():
    chunks = ["[Narration]\n", "You enter ", "the hall.", "\n[StateUpdates]\n", "{}"]
    out = _join(chunks)
    assert "You enter the hall." in out
    assert "[Narration]" not in out
    assert "[StateUpdates]" not in out
    assert "{}" not in out  # state block not streamed as narration


def test_handles_header_split_across_chunks():
    chunks = ["[Nar", "ration]", " Hello", " world", "[Stat", "eUpdates]{}"]
    out = _join(chunks)
    assert "[Narration]" not in out and "[Nar" not in out
    assert "[StateUpdates]" not in out and "[Stat" not in out
    assert "Hello world" in out


def test_no_tags_passthrough():
    chunks = ["Just ", "plain ", "narration."]
    assert _join(chunks) == "Just plain narration."
