from pathlib import Path

import polars as pl
import pytest

from riksdagen.load import load_all_voteringar, load_persons, load_votering

DATA_DIR = Path(__file__).parent / "data"
DOWNLOADS = Path(__file__).parent.parent.parent / "downloads"


@pytest.fixture(scope="session")
def votering_new() -> pl.DataFrame:
    return load_votering(DATA_DIR / "votering_new.csv")


@pytest.fixture(scope="session")
def votering_new_bom() -> pl.DataFrame:
    return load_votering(DATA_DIR / "votering_new_bom.csv")


@pytest.fixture(scope="session")
def votering_old() -> pl.DataFrame:
    return load_votering(DATA_DIR / "votering_old.csv")


@pytest.fixture(scope="session")
def persons() -> pl.DataFrame:
    return load_persons(DATA_DIR / "person.csv")


def test_votering_columns(votering_new: pl.DataFrame) -> None:
    expected = {
        "riksmote", "beteckning", "votering_id", "punkt", "namn",
        "intressent_id", "parti", "valkrets", "rost", "avser",
        "votering_nummer", "kon", "fodd_ar", "datum",
    }
    assert set(votering_new.columns) == expected


def test_votering_rost_values(votering_new: pl.DataFrame) -> None:
    valid = {"Ja", "Nej", "Frånvarande", "Avstår"}
    assert set(votering_new["rost"].unique().to_list()) <= valid


def test_votering_avser_lowercase(votering_new: pl.DataFrame) -> None:
    assert all(v == v.lower() for v in votering_new["avser"].unique().to_list())


def test_votering_datum_is_date(votering_new: pl.DataFrame) -> None:
    assert votering_new["datum"].dtype == pl.Date


def test_votering_no_bom_in_riksmote(votering_new: pl.DataFrame) -> None:
    assert all("﻿" not in v for v in votering_new["riksmote"].unique().to_list())


def test_votering_bom_stripped_from_data(votering_new_bom: pl.DataFrame) -> None:
    assert all("﻿" not in v for v in votering_new_bom["riksmote"].unique().to_list())


def test_old_format_loads(votering_old: pl.DataFrame) -> None:
    assert votering_old["riksmote"].unique().to_list() == ["1999/2000"]
    assert votering_old["datum"].dtype == pl.Date


def test_old_format_avser_normalized(votering_old: pl.DataFrame) -> None:
    # Old files have "Sakfrågan" (capital S) — must be normalized to lowercase
    assert all(v == v.lower() for v in votering_old["avser"].unique().to_list())


def test_old_format_kon_normalized(votering_old: pl.DataFrame) -> None:
    assert set(votering_old["kon"].unique().to_list()) <= {"man", "kvinna"}


def test_old_format_parti_uppercase(votering_old: pl.DataFrame) -> None:
    assert all(v == v.upper() for v in votering_old["parti"].unique().to_list())


def test_old_format_unknown_member_is_null(votering_old: pl.DataFrame) -> None:
    # "?" sentinel in intressent_id and fodd_ar must become null
    assert votering_old["intressent_id"].null_count() == 1
    assert votering_old["fodd_ar"].null_count() == 1


def test_persons_columns(persons: pl.DataFrame) -> None:
    assert "intressent_id" in persons.columns
    assert "parti" in persons.columns
    assert "status" in persons.columns


def test_persons_no_bom(persons: pl.DataFrame) -> None:
    for col in persons.columns:
        assert "﻿" not in col


def test_persons_fodd_ar_is_int(persons: pl.DataFrame) -> None:
    assert persons["fodd_ar"].dtype == pl.Int32


def test_persons_empty_fodd_ar_is_null(persons: pl.DataFrame) -> None:
    assert persons["fodd_ar"].null_count() == 1


def test_persons_tom_is_date(persons: pl.DataFrame) -> None:
    assert persons["tom"].dtype == pl.Date


def test_persons_tom_timestamp_truncated(persons: pl.DataFrame) -> None:
    # "2026-05-26 23:59:00" must parse to a Date, not fail
    non_null = persons["tom"].drop_nulls()
    assert len(non_null) == 1


def test_load_all_voteringar_concatenates(tmp_path: Path) -> None:
    import shutil
    shutil.copy(DATA_DIR / "votering_new.csv", tmp_path / "votering-202526.csv")
    shutil.copy(DATA_DIR / "votering_old.csv", tmp_path / "votering-19992000.csv")
    df = load_all_voteringar(tmp_path)
    sessions = set(df["riksmote"].unique().to_list())
    assert "2025/26" in sessions
    assert "1999/2000" in sessions


def test_load_all_voteringar_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_all_voteringar(tmp_path)


@pytest.mark.skipif(not DOWNLOADS.exists(), reason="downloads/ not present in this checkout")
def test_votering_all_sessions() -> None:
    df = load_all_voteringar(DOWNLOADS)
    sessions = set(df["riksmote"].unique().to_list())
    assert "1999/2000" in sessions
    assert "2025/26" in sessions
