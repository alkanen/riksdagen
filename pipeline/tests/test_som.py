"""Tests for riksdagen.som.train_som."""

from typing import Any

import numpy as np
import polars as pl

from riksdagen.config import Config
from riksdagen.som import train_som

_CFG = Config(
    sessions=["2022/23"],
    min_votes=1,
    grid_width=4,
    grid_height=4,
    party_colors={"S": "#FF0000"},
)


def _make_matrix(
    n_members: int = 10, n_props: int = 20, seed: int = 42
) -> pl.DataFrame:
    """Build a synthetic vote matrix matching build_vote_matrix output schema."""
    rng = np.random.default_rng(seed)
    values = rng.choice(
        [1.0, -1.0, 0.0, float("nan")],
        p=[0.4, 0.4, 0.1, 0.1],
        size=(n_members, n_props),
    )
    ids = [f"M{i:02d}" for i in range(n_members)]
    data: dict[str, list[Any]] = {"intressent_id": ids}
    for j in range(n_props):
        data[f"v{j:02d}__1"] = values[:, j].tolist()
    df = pl.DataFrame(data)
    return df.with_columns(
        [pl.col(f"v{j:02d}__1").cast(pl.Float32) for j in range(n_props)]
    )


# ── shape and columns ─────────────────────────────────────────────────────────


def test_assignments_has_correct_columns() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert assignments.columns == ["intressent_id", "grid_x", "grid_y"]


def test_assignments_has_one_row_per_member() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert assignments.shape[0] == matrix.shape[0]


# ── correctness ───────────────────────────────────────────────────────────────


def test_all_members_in_assignments() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert set(assignments["intressent_id"].to_list()) == set(
        matrix["intressent_id"].to_list()
    )


def test_grid_x_within_bounds() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert int(assignments["grid_x"].min()) >= 0  # type: ignore[arg-type]
    assert int(assignments["grid_x"].max()) < _CFG.grid_width  # type: ignore[arg-type]


def test_grid_y_within_bounds() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert int(assignments["grid_y"].min()) >= 0  # type: ignore[arg-type]
    assert int(assignments["grid_y"].max()) < _CFG.grid_height  # type: ignore[arg-type]


# ── types ─────────────────────────────────────────────────────────────────────


def test_grid_x_is_int32() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert assignments["grid_x"].dtype == pl.Int32


def test_grid_y_is_int32() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert assignments["grid_y"].dtype == pl.Int32


# ── determinism ───────────────────────────────────────────────────────────────


def test_same_seed_produces_same_assignments() -> None:
    matrix = _make_matrix()
    a1, _ = train_som(matrix, _CFG, seed=42, n_epochs=3)
    a2, _ = train_som(matrix, _CFG, seed=42, n_epochs=3)
    assert a1.equals(a2)


# ── row order ─────────────────────────────────────────────────────────────────


def test_row_order_matches_input_matrix() -> None:
    matrix = _make_matrix()
    assignments, _ = train_som(matrix, _CFG, n_epochs=1)
    assert assignments["intressent_id"].to_list() == matrix["intressent_id"].to_list()
