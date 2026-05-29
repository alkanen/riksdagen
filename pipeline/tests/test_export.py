"""Tests for riksdagen.export."""

import json
from pathlib import Path

import polars as pl
import pytest

from riksdagen.config import Config
from riksdagen.export import export_grid, write_export

_CFG = Config(
    sessions=["2022/23"],
    min_votes=1,
    grid_width=3,
    grid_height=2,
    party_colors={"S": "#E8112d", "M": "#52BDEC"},
)


def _make_assignments(rows: list[tuple[str, int, int]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "intressent_id": [r[0] for r in rows],
            "grid_x": pl.Series([r[1] for r in rows], dtype=pl.Int32),
            "grid_y": pl.Series([r[2] for r in rows], dtype=pl.Int32),
        }
    )


def _make_metadata(
    rows: list[tuple[str, str, str, str, int, int, bool]],
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "intressent_id": [r[0] for r in rows],
            "namn": [r[1] for r in rows],
            "parti": [r[2] for r in rows],
            "kon": [r[3] for r in rows],
            "fodd_ar": pl.Series([r[4] for r in rows], dtype=pl.Int32),
            "vote_count": pl.Series([r[5] for r in rows], dtype=pl.Int32),
            "low_confidence": [r[6] for r in rows],
        }
    )


# ── cell count ────────────────────────────────────────────────────────────────


def test_cell_count_equals_grid_size() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    assert len(result["cells"]) == _CFG.grid_width * _CFG.grid_height


def test_cells_have_row_and_col_keys() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    for cell in result["cells"]:
        assert "row" in cell
        assert "col" in cell


def test_cells_cover_all_positions() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    positions = {(c["row"], c["col"]) for c in result["cells"]}
    expected = {(r, c) for r in range(_CFG.grid_height) for c in range(_CFG.grid_width)}
    assert positions == expected


# ── empty cells ───────────────────────────────────────────────────────────────


def test_empty_cell_has_no_members() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    for cell in result["cells"]:
        assert cell["members"] == []


def test_empty_cell_has_null_dominant_party() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    for cell in result["cells"]:
        assert cell["dominant_party"] is None


# ── member placement ──────────────────────────────────────────────────────────


def test_member_appears_in_correct_cell() -> None:
    assignments = _make_assignments([("M01", 1, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 1)
    assert len(cell["members"]) == 1
    assert cell["members"][0]["intressent_id"] == "M01"


def test_other_cells_remain_empty_when_one_member_assigned() -> None:
    assignments = _make_assignments([("M01", 1, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    result = export_grid(assignments, metadata, _CFG)
    for cell in result["cells"]:
        if cell["row"] == 0 and cell["col"] == 1:
            continue
        assert cell["members"] == []


# ── dominant party ────────────────────────────────────────────────────────────


def test_dominant_party_is_plurality_party() -> None:
    assignments = _make_assignments([("M01", 0, 0), ("M02", 0, 0), ("M03", 0, 0)])
    metadata = _make_metadata(
        [
            ("M01", "Anna", "S", "kvinna", 1980, 100, False),
            ("M02", "Bjorn", "S", "man", 1975, 120, False),
            ("M03", "Carl", "M", "man", 1970, 80, False),
        ]
    )
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    assert cell["dominant_party"] == "S"


def test_dominant_party_tie_broken_alphabetically() -> None:
    assignments = _make_assignments([("M01", 0, 0), ("M02", 0, 0)])
    metadata = _make_metadata(
        [
            ("M01", "Anna", "M", "kvinna", 1980, 100, False),
            ("M02", "Bjorn", "S", "man", 1975, 120, False),
        ]
    )
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    assert cell["dominant_party"] == "M"


# ── member fields ─────────────────────────────────────────────────────────────


def test_low_confidence_propagated() -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 5, True)])
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    assert cell["members"][0]["low_confidence"] is True


def test_member_metadata_fields() -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 312, False)])
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    m = cell["members"][0]
    assert m["metadata"] == {"kon": "kvinna", "fodd_ar": 1980, "vote_count": 312}


# ── top-level fields ──────────────────────────────────────────────────────────


def test_grid_dimensions_match_config() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    assert result["grid"] == {"width": _CFG.grid_width, "height": _CFG.grid_height}


def test_party_colors_match_config() -> None:
    assignments = _make_assignments([])
    metadata = _make_metadata([])
    result = export_grid(assignments, metadata, _CFG)
    assert result["party_colors"] == _CFG.party_colors


# ── JSON round-trip ───────────────────────────────────────────────────────────


def test_output_round_trips_through_json() -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    metadata = _make_metadata([("M01", "Anna Öberg", "S", "kvinna", 1980, 100, False)])
    result = export_grid(assignments, metadata, _CFG)
    restored = json.loads(json.dumps(result, ensure_ascii=False))
    assert restored == result


# ── write_export ──────────────────────────────────────────────────────────────


def test_write_export_creates_valid_json_file(tmp_path: Path) -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    result = export_grid(assignments, metadata, _CFG)
    out = tmp_path / "export.json"
    write_export(result, out)
    restored = json.loads(out.read_text(encoding="utf-8"))
    assert restored == result


def test_write_export_creates_missing_parent_directories(tmp_path: Path) -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    result = export_grid(assignments, metadata, _CFG)
    out = tmp_path / "a" / "b" / "export.json"
    write_export(result, out)
    assert out.exists()


# ── validation ────────────────────────────────────────────────────────────────


def test_raises_when_assignment_id_missing_from_metadata() -> None:
    assignments = _make_assignments([("M01", 0, 0), ("M99", 1, 0)])
    metadata = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    with pytest.raises(ValueError, match="M99"):
        export_grid(assignments, metadata, _CFG)


# ── open metadata object ──────────────────────────────────────────────────────


def test_extra_metadata_columns_forwarded_automatically() -> None:
    assignments = _make_assignments([("M01", 0, 0)])
    base = _make_metadata([("M01", "Anna", "S", "kvinna", 1980, 100, False)])
    extended = base.with_columns(pl.lit("boomer").alias("age_cohort"))
    result = export_grid(assignments, extended, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    assert cell["members"][0]["metadata"]["age_cohort"] == "boomer"


# ── member ordering ───────────────────────────────────────────────────────────


def test_members_within_cell_sorted_by_intressent_id() -> None:
    assignments = _make_assignments([("M03", 0, 0), ("M01", 0, 0), ("M02", 0, 0)])
    metadata = _make_metadata(
        [
            ("M01", "Anna", "S", "kvinna", 1980, 100, False),
            ("M02", "Bjorn", "S", "man", 1975, 120, False),
            ("M03", "Carl", "M", "man", 1970, 80, False),
        ]
    )
    result = export_grid(assignments, metadata, _CFG)
    cell = next(c for c in result["cells"] if c["row"] == 0 and c["col"] == 0)
    ids = [m["intressent_id"] for m in cell["members"]]
    assert ids == sorted(ids)
