import re
from pathlib import Path

import pytest
import yaml

from riksdagen.config import Config, load_config

_VALID: dict[str, object] = {
    "sessions": ["2022/23", "2023/24"],
    "min_votes": 50,
    "grid_width": 10,
    "grid_height": 8,
    "party_colors": {"S": "#E8112d", "M": "#52BDEC"},
}


def _write(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_default_path_is_used_when_no_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "pipeline" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text(yaml.safe_dump(_VALID), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.min_votes == 50


def test_valid_config_round_trips(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, _VALID))
    assert cfg.sessions == ["2022/23", "2023/24"]
    assert cfg.min_votes == 50
    assert cfg.grid_width == 10
    assert cfg.grid_height == 8
    assert cfg.party_colors == {"S": "#E8112d", "M": "#52BDEC"}


def test_returns_config_dataclass(tmp_path: Path) -> None:
    assert isinstance(load_config(_write(tmp_path, _VALID)), Config)


@pytest.mark.parametrize("missing_key", list(_VALID))
def test_missing_required_key_raises(tmp_path: Path, missing_key: str) -> None:
    data = {k: v for k, v in _VALID.items() if k != missing_key}
    with pytest.raises(ValueError, match=missing_key):
        load_config(_write(tmp_path, data))


def test_unknown_key_raises(tmp_path: Path) -> None:
    data = {**_VALID, "surprise": 42}
    with pytest.raises(ValueError, match="surprise"):
        load_config(_write(tmp_path, data))


@pytest.mark.parametrize("key", ["min_votes", "grid_width", "grid_height"])
@pytest.mark.parametrize("bad_value", [0, -1, "ten", 1.5])
def test_non_positive_integer_raises(
    tmp_path: Path, key: str, bad_value: object
) -> None:
    data = {**_VALID, key: bad_value}
    with pytest.raises(ValueError, match=key):
        load_config(_write(tmp_path, data))


# --- I/O and YAML parse errors ---


def test_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"
    pattern = f"Config file not found: {re.escape(str(path))}"
    with pytest.raises(FileNotFoundError, match=pattern):
        load_config(path)


def test_invalid_yaml_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValueError, match=str(path)):
        load_config(path)


# --- YAML root type validation ---


def test_empty_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_config(path)


def test_yaml_list_at_root_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("- sessions\n- min_votes\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_config(path)


# --- sessions validation ---


def test_sessions_empty_list_raises(tmp_path: Path) -> None:
    data = {**_VALID, "sessions": []}
    with pytest.raises(ValueError, match="sessions"):
        load_config(_write(tmp_path, data))


def test_sessions_not_a_list_raises(tmp_path: Path) -> None:
    data = {**_VALID, "sessions": "2022/23"}
    with pytest.raises(ValueError, match="sessions"):
        load_config(_write(tmp_path, data))


def test_sessions_non_string_element_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    # Write raw YAML so the integer is not quoted by safe_dump.
    path.write_text(
        "sessions: [2022]\nmin_votes: 50\ngrid_width: 10\n"
        "grid_height: 8\nparty_colors: {S: '#E8112d'}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sessions"):
        load_config(path)


# --- party_colors validation ---


def test_party_colors_not_a_dict_raises(tmp_path: Path) -> None:
    data = {**_VALID, "party_colors": ["S", "M"]}
    with pytest.raises(ValueError, match="party_colors"):
        load_config(_write(tmp_path, data))


@pytest.mark.parametrize("bad_key", ["s", "S ", " S", "M1", "1S", ""])
def test_party_colors_invalid_key_raises(tmp_path: Path, bad_key: str) -> None:
    data = {**_VALID, "party_colors": {bad_key: "#E8112d"}}
    with pytest.raises(ValueError, match="party_colors"):
        load_config(_write(tmp_path, data))


def test_party_colors_non_string_value_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "sessions: ['2022/23']\nmin_votes: 50\ngrid_width: 10\n"
        "grid_height: 8\nparty_colors: {S: 123}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="party_colors"):
        load_config(path)


@pytest.mark.parametrize(
    "bad_value",
    ["red", "#GGG", "#GGGGGG", "#12345", "#1234567", "", "E8112d"],
)
def test_party_colors_invalid_hex_raises(tmp_path: Path, bad_value: str) -> None:
    data = {**_VALID, "party_colors": {"S": bad_value}}
    with pytest.raises(ValueError, match="party_colors"):
        load_config(_write(tmp_path, data))
