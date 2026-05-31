"""Smoke test for the riksdagen CLI entry point."""

import json
import sys
from pathlib import Path

import pytest

# Votering CSV fixture data (new format: no header row).
# Built as tuples to avoid E501 — each field is wrapped in quotes by the joiner.
_VOTERING_ROWS: list[tuple[str, ...]] = [
    # Proposition 1
    (
        "2025/26",
        "JuU1",
        "VOTE-001",
        "1",
        "Anna S",
        "0000000000001",
        "S",
        "Stockholm",
        "Ja",
        "sakfrågan",
        "1",
        "kvinna",
        "1980",
        "2026-01-01",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-001",
        "1",
        "Bo K",
        "0000000000002",
        "M",
        "Göteborg",
        "Nej",
        "sakfrågan",
        "1",
        "man",
        "1975",
        "2026-01-01",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-001",
        "1",
        "Cecilia B",
        "0000000000003",
        "SD",
        "Malmö",
        "Ja",
        "sakfrågan",
        "1",
        "kvinna",
        "1985",
        "2026-01-01",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-001",
        "1",
        "David E",
        "0000000000004",
        "V",
        "Uppsala",
        "Nej",
        "sakfrågan",
        "1",
        "man",
        "1990",
        "2026-01-01",
    ),
    # Proposition 2 (PCA init needs ≥ 2 features)
    (
        "2025/26",
        "JuU1",
        "VOTE-002",
        "1",
        "Anna S",
        "0000000000001",
        "S",
        "Stockholm",
        "Nej",
        "sakfrågan",
        "2",
        "kvinna",
        "1980",
        "2026-01-28",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-002",
        "1",
        "Bo K",
        "0000000000002",
        "M",
        "Göteborg",
        "Ja",
        "sakfrågan",
        "2",
        "man",
        "1975",
        "2026-01-28",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-002",
        "1",
        "Cecilia B",
        "0000000000003",
        "SD",
        "Malmö",
        "Nej",
        "sakfrågan",
        "2",
        "kvinna",
        "1985",
        "2026-01-28",
    ),
    (
        "2025/26",
        "JuU1",
        "VOTE-002",
        "1",
        "David E",
        "0000000000004",
        "V",
        "Uppsala",
        "Ja",
        "sakfrågan",
        "2",
        "man",
        "1990",
        "2026-01-28",
    ),
]
_VOTERING_CSV = (
    "\n".join(",".join(f'"{f}"' for f in row) for row in _VOTERING_ROWS) + "\n"
)

_CONFIG_YAML = """\
sessions:
  - "2025/26"
min_votes: 1
grid_width: 2
grid_height: 2
party_colors:
  S: "#E8112d"
  M: "#52BDEC"
  SD: "#DDDD00"
  V: "#DA291C"
"""


@pytest.fixture()
def fixture_dir(tmp_path: Path) -> Path:
    """Populate tmp_path with a downloads dir and a config file."""
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    (downloads / "votering-2025-26.csv").write_text(_VOTERING_CSV, encoding="utf-8")
    (tmp_path / "config.yaml").write_text(_CONFIG_YAML, encoding="utf-8")
    return tmp_path


def test_cli_produces_valid_json(
    fixture_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = fixture_dir / "out" / "data.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "riksdagen",
            "--config",
            str(fixture_dir / "config.yaml"),
            "--downloads",
            str(fixture_dir / "downloads"),
            "--out",
            str(out),
        ],
    )

    from riksdagen.__main__ import main

    main()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["grid"] == {"width": 2, "height": 2}
    assert len(data["cells"]) == 4
    assert "party_colors" in data


def test_cli_exits_on_missing_downloads(
    fixture_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "riksdagen",
            "--config",
            str(fixture_dir / "config.yaml"),
            "--downloads",
            str(fixture_dir / "nonexistent"),
            "--out",
            str(fixture_dir / "data.json"),
        ],
    )

    from riksdagen.__main__ import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code  # non-zero / non-None → error exit
