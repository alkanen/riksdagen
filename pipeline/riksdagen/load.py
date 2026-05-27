"""Load Riksdagen CSV downloads into Polars DataFrames."""

from pathlib import Path

import polars as pl

# Canonical column order for all votering DataFrames.
VOTERING_COLUMNS = [
    "riksmote",  # "2025/26"
    "beteckning",  # committee + number, e.g. "JuU22"
    "votering_id",  # vote identifier
    "punkt",  # sub-point within the proposition
    "namn",  # member full name
    "intressent_id",  # member ID (links to person.csv Id column)
    "parti",  # party abbreviation
    "valkrets",  # constituency
    "rost",  # Ja / Nej / Frånvarande / Avstår
    "avser",  # sakfrågan / motivfrågan
    "votering_nummer",
    "kon",  # man / kvinna (older files use M / K)
    "fodd_ar",  # birth year
    "datum",  # vote date
]

# Pre-2002/03 files have a header row with different column names.
_OLD_COLUMN_MAP = {
    "rm": "riksmote",
    "banknummer": "votering_nummer",
    "fodd": "fodd_ar",
}

# Column names as they appear in the old-format header (before renaming).
_OLD_VOTERING_COLUMNS = [
    "rm",
    "beteckning",
    "punkt",
    "votering_id",
    "namn",
    "intressent_id",
    "parti",
    "valkrets",
    "rost",
    "avser",
    "banknummer",
    "kon",
    "fodd",
    "datum",
]

# Explicit all-String schemas — we cast to final types in _normalize_votering
# after handling "?" sentinels and other quirks that require string-level ops.
_VOTERING_STRING_SCHEMA = {col: pl.String for col in VOTERING_COLUMNS}
_OLD_VOTERING_STRING_SCHEMA = {col: pl.String for col in _OLD_VOTERING_COLUMNS}

PERSON_COLUMN_MAP = {
    "Förnamn": "fornamn",
    "Efternamn": "efternamn",
    "Iort": "iort",
    "Parti": "parti",
    "Id": "intressent_id",
    "Kön": "kon",
    "Född": "fodd_ar",
    "Valkrets": "valkrets",
    "Status": "status",
    "Webbadress": "webbadress",
    "Epostadress": "epostadress",
    "Telefonnummer": "telefonnummer",
    "Titel": "titel",
    "Uppdragstyp": "uppdragstyp",
    "Uppdragsorgan": "uppdragsorgan",
    "Uppdragsroll": "uppdragsroll",
    "Uppdragsrollstatus": "uppdragsrollstatus",
    "From": "fran",
    "Tom": "tom",
}

_PERSON_STRING_SCHEMA = {col: pl.String for col in PERSON_COLUMN_MAP}

_BOM = b"\xef\xbb\xbf"  # UTF-8 BOM as bytes
_STR_BOM = "\ufeff"  # UTF-8 BOM as str (U+FEFF)


def _has_old_header(path: Path) -> bool:
    """Return True for pre-2002/03 files that start with a 'rm,...' header."""
    with open(path, "rb") as f:
        chunk = f.read(20)
    return chunk.removeprefix(_BOM).startswith(b"rm,")


def _strip_bom(df: pl.DataFrame) -> pl.DataFrame:
    """Strip BOM from column names and from the riksmote column value.

    In headerless files the BOM lands in the first data cell (riksmote);
    in headered files it lands in the first column name.
    """
    df = df.rename({col: col.lstrip(_STR_BOM) for col in df.columns})
    if "riksmote" in df.columns:
        df = df.with_columns(pl.col("riksmote").str.strip_chars(_STR_BOM))
    return df


def _normalize_votering(df: pl.DataFrame) -> pl.DataFrame:
    """Reorder columns, cast types, and smooth over old-format quirks."""
    df = df.select(VOTERING_COLUMNS)
    return df.with_columns(
        pl.col("punkt").cast(pl.Int32),
        pl.col("votering_nummer").cast(pl.Int32),
        pl.when(pl.col("fodd_ar").is_in(["", "?"]))
        .then(None)
        .otherwise(pl.col("fodd_ar"))
        .cast(pl.Int32)
        .alias("fodd_ar"),
        pl.when(pl.col("intressent_id") == "?")
        .then(None)
        .otherwise(pl.col("intressent_id"))
        .alias("intressent_id"),
        pl.col("datum").str.to_date(format="%Y-%m-%d", strict=False),
        pl.col("avser").str.to_lowercase(),
        # Old files (pre-2002) use single-letter kon codes and lowercase parti.
        pl.col("kon").replace(["K", "M"], ["kvinna", "man"]),
        pl.col("parti").str.to_uppercase(),
    )


def load_votering(path: Path) -> pl.DataFrame:
    if _has_old_header(path):
        df = pl.read_csv(
            path,
            has_header=True,
            schema_overrides=_OLD_VOTERING_STRING_SCHEMA,
            encoding="utf8",
        )
        df = _strip_bom(df)
        df = df.rename({col: _OLD_COLUMN_MAP.get(col, col) for col in df.columns})
    else:
        df = pl.read_csv(
            path,
            has_header=False,
            schema=_VOTERING_STRING_SCHEMA,
            encoding="utf8",
        )
        df = _strip_bom(df)
    return _normalize_votering(df)


def load_all_voteringar(downloads_dir: Path) -> pl.DataFrame:
    paths = sorted(downloads_dir.glob("votering-*.csv"))
    if not paths:
        raise FileNotFoundError(f"No votering-*.csv files found in {downloads_dir}")
    # rechunk=False avoids a full-copy consolidation pass; caller can rechunk if needed.
    return pl.concat((load_votering(p) for p in paths), rechunk=False)


def load_persons(path: Path) -> pl.DataFrame:
    df = pl.read_csv(
        path,
        has_header=True,
        schema_overrides=_PERSON_STRING_SCHEMA,
        encoding="utf8",
    )
    df = _strip_bom(df)
    df = df.rename(PERSON_COLUMN_MAP)
    return df.with_columns(
        pl.when(pl.col("fodd_ar").is_in(["", "?"]))
        .then(None)
        .otherwise(pl.col("fodd_ar"))
        .cast(pl.Int32)
        .alias("fodd_ar"),
        pl.col("fran").str.to_date(format="%Y-%m-%d", strict=False),
        # tom has timestamps like "1976-10-04 23:59:00" — truncate to date
        pl.col("tom").str.slice(0, 10).str.to_date(format="%Y-%m-%d", strict=False),
    )
