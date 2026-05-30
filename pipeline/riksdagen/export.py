"""Serialise trained SOM results to a static JSON file for frontend consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

from riksdagen.config import Config

# Columns consumed as top-level member fields; everything else in metadata goes
# into the open `metadata` object so new pipeline columns appear automatically.
_FIXED_COLS: frozenset[str] = frozenset(
    {"intressent_id", "namn", "parti", "low_confidence", "grid_x", "grid_y"}
)


def export_grid(
    assignments: pl.DataFrame,
    metadata: pl.DataFrame,
    config: Config,
) -> dict[str, Any]:
    """Build the JSON-serialisable export dict from SOM results.

    Args:
        assignments: DataFrame with intressent_id, grid_x, grid_y.
        metadata:    DataFrame with intressent_id, namn, parti, low_confidence,
                     and any number of additional metadata columns (kon, fodd_ar,
                     vote_count, …).  Extra columns are forwarded into each
                     member's open ``metadata`` object automatically.
        config:      Pipeline config supplying grid dimensions and party colors.

    Returns:
        A dict matching the frontend JSON contract.

    Raises:
        ValueError: if any intressent_id in assignments is absent from metadata.
    """
    missing = set(assignments["intressent_id"].to_list()) - set(
        metadata["intressent_id"].to_list()
    )
    if missing:
        raise ValueError(
            f"Assignments contain intressent_ids not found in metadata: "
            f"{sorted(missing)}"
        )

    joined = assignments.join(metadata, on="intressent_id").sort("intressent_id")
    meta_cols = [c for c in joined.columns if c not in _FIXED_COLS]

    # Build a cell → members dict in a single pass over the joined rows.
    cell_map: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for r in joined.iter_rows(named=True):
        key = (int(r["grid_y"]), int(r["grid_x"]))
        cell_map.setdefault(key, []).append(
            {
                "intressent_id": r["intressent_id"],
                "namn": r["namn"],
                "parti": r["parti"],
                "low_confidence": bool(r["low_confidence"]),
                "metadata": {col: r[col] for col in meta_cols},
            }
        )

    cells: list[dict[str, Any]] = []
    for row in range(config.grid_height):
        for col in range(config.grid_width):
            members = cell_map.get((row, col), [])
            cells.append(
                {
                    "row": row,
                    "col": col,
                    "dominant_party": _dominant_party(members),
                    "members": members,
                }
            )

    return {
        "grid": {"width": config.grid_width, "height": config.grid_height},
        "party_colors": dict(config.party_colors),
        "cells": cells,
    }


def write_export(data: dict[str, Any], path: Path) -> None:
    """Write the export dict to *path* as UTF-8 JSON, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _dominant_party(members: list[dict[str, Any]]) -> str | None:
    if not members:
        return None
    counts: dict[str, int] = {}
    for m in members:
        counts[str(m["parti"])] = counts.get(str(m["parti"]), 0) + 1
    return min(
        counts,
        key=lambda p: (-counts[p], p),
    )
