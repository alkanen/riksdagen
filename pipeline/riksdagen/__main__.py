"""CLI entry point: load → vectors → SOM → export."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from riksdagen.config import load_config
from riksdagen.export import export_grid, write_export
from riksdagen.load import load_all_voteringar
from riksdagen.som import train_som
from riksdagen.vectors import build_vote_matrix

# Anchor defaults to the repo root so the CLI works regardless of the
# caller's cwd (e.g. `cd pipeline && uv run riksdagen` still resolves
# correctly).  __file__ is the installed source file for editable installs.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG = _REPO_ROOT / "pipeline" / "config.yaml"
_DEFAULT_DOWNLOADS = _REPO_ROOT / "downloads"
_DEFAULT_OUT = _REPO_ROOT / "frontend" / "public" / "data.json"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Riksdagen SOM and export grid JSON."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        metavar="PATH",
        help=f"Config YAML file (default: {_DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--downloads",
        type=Path,
        default=_DEFAULT_DOWNLOADS,
        metavar="DIR",
        help=(
            f"Directory containing votering-*.csv files (default: {_DEFAULT_DOWNLOADS})"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        metavar="PATH",
        help=f"Output JSON path (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args()

    if not args.downloads.is_dir():
        sys.exit(f"Error: downloads directory not found: {args.downloads}")

    _log(f"Loading config from {args.config} …")
    cfg = load_config(args.config)

    _log(f"Loading voteringar from {args.downloads} …")
    votering = load_all_voteringar(args.downloads)
    n_sessions = len(set(votering["riksmote"].to_list()))
    _log(f"  {votering.height:,} rows across {n_sessions} sessions")

    _log("Building vote matrix …")
    matrix, metadata = build_vote_matrix(votering, cfg.sessions, cfg.min_votes)
    n_props = matrix.shape[1] - 1
    _log(f"  {matrix.shape[0]} members × {n_props} propositions")

    _log(f"Training SOM ({cfg.grid_width}×{cfg.grid_height}) …")
    assignments, _ = train_som(matrix, cfg)
    _log("  Done.")

    _log("Exporting …")
    data = export_grid(assignments, metadata, cfg)
    write_export(data, args.out)
    _log(f"  Written → {args.out}")


if __name__ == "__main__":
    main()
