"""Tests for riksdagen.vectors.build_vote_matrix."""

import datetime
import math
from typing import Any

import polars as pl
import pytest

from riksdagen.vectors import build_vote_matrix

_SCHEMA: dict[str, Any] = {
    "riksmote": pl.String,
    "votering_id": pl.String,
    "punkt": pl.Int32,
    "intressent_id": pl.String,
    "namn": pl.String,
    "parti": pl.String,
    "kon": pl.String,
    "fodd_ar": pl.Int32,
    "rost": pl.String,
    "avser": pl.String,
    "datum": pl.Date,
}


def _row(
    *,
    riksmote: str = "2022/23",
    votering_id: str = "v1",
    punkt: int = 1,
    intressent_id: str | None = "A",
    namn: str = "Anna",
    parti: str = "S",
    kon: str = "kvinna",
    fodd_ar: int | None = 1980,
    rost: str = "Ja",
    avser: str = "sakfrågan",
    datum: datetime.date = datetime.date(2022, 1, 1),
) -> dict[str, Any]:
    return {
        "riksmote": riksmote,
        "votering_id": votering_id,
        "punkt": punkt,
        "intressent_id": intressent_id,
        "namn": namn,
        "parti": parti,
        "kon": kon,
        "fodd_ar": fodd_ar,
        "rost": rost,
        "avser": avser,
        "datum": datum,
    }


def _make_votering(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=_SCHEMA)


# ── shape ─────────────────────────────────────────────────────────────────────


def test_matrix_has_one_row_per_member_and_one_col_per_proposition() -> None:
    df = _make_votering(
        [
            _row(intressent_id="A"),
            _row(intressent_id="B"),
        ]
    )
    matrix, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix.shape == (2, 2)  # intressent_id + 1 prop col
    assert metadata.shape == (2, 7)


# ── vote encoding ─────────────────────────────────────────────────────────────


def test_ja_encodes_to_1() -> None:
    df = _make_votering([_row(rost="Ja")])
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix["v1__1"][0] == pytest.approx(1.0)


def test_nej_encodes_to_minus1() -> None:
    df = _make_votering([_row(rost="Nej")])
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix["v1__1"][0] == pytest.approx(-1.0)


def test_avstar_encodes_to_0() -> None:
    df = _make_votering([_row(rost="Avstår")])
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix["v1__1"][0] == pytest.approx(0.0)


def test_unknown_rost_raises() -> None:
    df = _make_votering([_row(rost="Ogiltig")])
    with pytest.raises(ValueError, match="Ogiltig"):
        build_vote_matrix(df, sessions=["2022/23"], min_votes=1)


def test_null_intressent_id_rows_excluded() -> None:
    df = _make_votering(
        [
            _row(intressent_id=None, rost="Ja"),
            _row(intressent_id="B", rost="Nej"),
        ]
    )
    matrix, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix.shape[0] == 1
    assert matrix["intressent_id"].to_list() == ["B"]


def test_duplicate_votes_raises() -> None:
    df = _make_votering(
        [
            _row(intressent_id="A", votering_id="v1", punkt=1, rost="Ja"),
            _row(intressent_id="A", votering_id="v1", punkt=1, rost="Nej"),
        ]
    )
    with pytest.raises(ValueError, match="uplicate"):
        build_vote_matrix(df, sessions=["2022/23"], min_votes=1)


def test_metadata_parti_reflects_most_recent_datum() -> None:
    df = _make_votering(
        [
            _row(votering_id="v1", parti="S", datum=datetime.date(2022, 1, 1)),
            _row(votering_id="v2", parti="M", datum=datetime.date(2023, 1, 1)),
        ]
    )
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert metadata.filter(pl.col("intressent_id") == "A")["parti"][0] == "M"


def test_franvaro_encodes_to_nan() -> None:
    df = _make_votering([_row(rost="Frånvarande")])
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert math.isnan(matrix["v1__1"][0])


# ── filtering ─────────────────────────────────────────────────────────────────


def test_motivfragan_rows_not_included_as_propositions() -> None:
    df = _make_votering(
        [
            _row(votering_id="v1", avser="sakfrågan"),
            _row(votering_id="v2", avser="motivfrågan"),
        ]
    )
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    prop_cols = [c for c in matrix.columns if c != "intressent_id"]
    assert len(prop_cols) == 1
    assert "v2__1" not in matrix.columns


def test_sessions_outside_list_excluded() -> None:
    df = _make_votering(
        [
            _row(riksmote="2022/23", votering_id="v1"),
            _row(riksmote="2021/22", votering_id="v2"),
        ]
    )
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    prop_cols = [c for c in matrix.columns if c != "intressent_id"]
    assert len(prop_cols) == 1
    assert "v2__1" not in matrix.columns


# ── low_confidence ────────────────────────────────────────────────────────────


def test_low_confidence_when_vote_count_below_threshold() -> None:
    df = _make_votering([_row(rost="Ja")])
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=2)
    assert metadata.filter(pl.col("intressent_id") == "A")["low_confidence"][0] is True


def test_not_low_confidence_when_vote_count_at_threshold() -> None:
    df = _make_votering(
        [
            _row(votering_id="v1", rost="Ja"),
            _row(votering_id="v2", rost="Nej"),
        ]
    )
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=2)
    assert metadata.filter(pl.col("intressent_id") == "A")["low_confidence"][0] is False


# ── all-Frånvarande member ────────────────────────────────────────────────────


def test_all_franvaro_member_has_nan_matrix_row() -> None:
    df = _make_votering(
        [
            _row(intressent_id="A", rost="Ja"),
            _row(intressent_id="B", rost="Frånvarande"),
        ]
    )
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert math.isnan(matrix.filter(pl.col("intressent_id") == "B")["v1__1"][0])


def test_all_franvaro_member_has_zero_vote_count() -> None:
    df = _make_votering(
        [
            _row(intressent_id="A", rost="Ja"),
            _row(intressent_id="B", rost="Frånvarande"),
        ]
    )
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert metadata.filter(pl.col("intressent_id") == "B")["vote_count"][0] == 0


# ── vote_count ────────────────────────────────────────────────────────────────


def test_vote_count_excludes_franvaro() -> None:
    df = _make_votering(
        [
            _row(votering_id="v1", rost="Ja"),
            _row(votering_id="v2", rost="Frånvarande"),
            _row(votering_id="v3", rost="Nej"),
        ]
    )
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert metadata.filter(pl.col("intressent_id") == "A")["vote_count"][0] == 2


# ── row alignment ─────────────────────────────────────────────────────────────


def test_matrix_and_metadata_have_same_row_order() -> None:
    df = _make_votering(
        [
            _row(intressent_id="B"),
            _row(intressent_id="A"),
        ]
    )
    matrix, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert matrix["intressent_id"].to_list() == metadata["intressent_id"].to_list()


# ── types ─────────────────────────────────────────────────────────────────────


def test_prop_columns_are_float32() -> None:
    df = _make_votering([_row()])
    matrix, _ = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    for col in [c for c in matrix.columns if c != "intressent_id"]:
        assert matrix[col].dtype == pl.Float32


def test_metadata_columns_are_correct() -> None:
    df = _make_votering([_row()])
    _, metadata = build_vote_matrix(df, sessions=["2022/23"], min_votes=1)
    assert metadata.columns == [
        "intressent_id",
        "namn",
        "parti",
        "kon",
        "fodd_ar",
        "vote_count",
        "low_confidence",
    ]
