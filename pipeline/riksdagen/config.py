"""Load and validate the pipeline YAML config file."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

_REQUIRED: frozenset[str] = frozenset(
    {"sessions", "min_votes", "grid_width", "grid_height", "party_colors"}
)
_POSITIVE_INT_KEYS: frozenset[str] = frozenset(
    {"min_votes", "grid_width", "grid_height"}
)

# Relative to the current working directory. The default assumes invocation
# from the repo root (e.g. `uv run riksdagen`). Pass an explicit path when
# running from another directory. The CLI (issue #8) will expose --config.
DEFAULT_CONFIG_PATH = Path("pipeline/config.yaml")


@dataclass
class Config:
    sessions: list[str]
    min_votes: int
    grid_width: int
    grid_height: int
    party_colors: dict[str, str]


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load and validate the pipeline config from a YAML file.

    When called with no argument, resolves *path* relative to the current
    working directory (expected to be the repo root when using ``uv run``).
    Pass an explicit path to override, e.g. for tests or multiple configs.
    """
    try:
        with path.open(encoding="utf-8") as f:
            raw: Any = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}") from None
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse config file {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(
            f"Config file must be a YAML mapping at the root, got {type(raw).__name__}"
        )
    if not all(isinstance(k, str) for k in raw):
        raise ValueError("Config file mapping keys must all be strings")
    data: dict[str, Any] = raw

    unknown = set(data) - _REQUIRED
    if unknown:
        raise ValueError(f"Unknown config keys: {sorted(unknown)}")

    missing = _REQUIRED - set(data)
    if missing:
        raise ValueError(
            f"Missing required config key{'s' if len(missing) > 1 else ''}: "
            f"{', '.join(sorted(missing))}"
        )

    for key in sorted(_POSITIVE_INT_KEYS):
        val = data[key]
        if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
            raise ValueError(
                f"Config key '{key}' must be a positive integer, got {val!r}"
            )

    sessions = data["sessions"]
    if (
        not isinstance(sessions, list)
        or not sessions
        or not all(isinstance(s, str) for s in sessions)
    ):
        raise ValueError("Config key 'sessions' must be a non-empty list of strings")

    party_colors = data["party_colors"]
    if not isinstance(party_colors, dict):
        raise ValueError("Config key 'party_colors' must be a mapping")
    bad_keys = [
        k
        for k in party_colors
        if not isinstance(k, str) or not (k.isalpha() and k.isupper())
    ]
    if bad_keys:
        raise ValueError(
            f"Config key 'party_colors' keys must be uppercase strings, got: {bad_keys}"
        )
    bad_value_keys = sorted(
        k
        for k, v in party_colors.items()
        if not isinstance(v, str) or not _HEX_COLOR_RE.match(v)
    )
    if bad_value_keys:
        raise ValueError(
            f"Config key 'party_colors' values must be hex colors (#RRGGBB), "
            f"invalid for keys: {bad_value_keys}"
        )

    return Config(
        sessions=sessions,
        min_votes=data["min_votes"],
        grid_width=data["grid_width"],
        grid_height=data["grid_height"],
        party_colors=party_colors,
    )
