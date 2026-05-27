"""Transform a votering DataFrame into a member × proposition matrix and metadata."""

import math

import polars as pl

_KNOWN_ROST: frozenset[str] = frozenset({"Ja", "Nej", "Avstår", "Frånvarande"})


def build_vote_matrix(
    votering: pl.DataFrame,
    sessions: list[str],
    min_votes: int,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build a member × proposition vote matrix and per-member metadata.

    Returns:
        (matrix, metadata) — one row per member in the same sorted order.

        matrix columns: "intressent_id" + one Float32 column per sakfrågan
            proposition, named "{votering_id}__{punkt}". Values: Ja=1.0,
            Nej=−1.0, Avstår=0.0, Frånvarande=NaN. Absent-member cells
            (member not in parliament for that proposition) are also NaN.

        metadata columns: intressent_id, namn, parti, kon, fodd_ar (Int32),
            vote_count (Int32), low_confidence (Bool). Metadata fields reflect
            the most recent row by datum for each member.

    Raises:
        ValueError: if any rost value outside the four known categories is found,
            or if any (intressent_id, proposition) pair has duplicate votes.
    """
    filtered = votering.filter(
        (pl.col("avser") == "sakfrågan")
        & pl.col("riksmote").is_in(sessions)
        & pl.col("intressent_id").is_not_null()
    )

    unknown_rost = set(filtered["rost"].unique().to_list()) - _KNOWN_ROST
    if unknown_rost:
        raise ValueError(f"Unexpected rost values: {sorted(unknown_rost)}")

    filtered = filtered.with_columns(
        pl.when(pl.col("rost") == "Ja")
        .then(pl.lit(1.0, dtype=pl.Float32))
        .when(pl.col("rost") == "Nej")
        .then(pl.lit(-1.0, dtype=pl.Float32))
        .when(pl.col("rost") == "Avstår")
        .then(pl.lit(0.0, dtype=pl.Float32))
        .otherwise(pl.lit(math.nan, dtype=pl.Float32))  # Frånvarande
        .alias("_vote"),
        (pl.col("votering_id") + "__" + pl.col("punkt").cast(pl.String)).alias("_prop"),
    )

    dupes = (
        filtered.group_by(["intressent_id", "_prop"])
        .agg(pl.len().alias("n"))
        .filter(pl.col("n") > 1)
    )
    if dupes.height > 0:
        raise ValueError(
            f"Duplicate votes: {dupes.height} (member, proposition) pair(s) "
            "appear more than once"
        )

    matrix = filtered.pivot(
        on="_prop",
        index="intressent_id",
        values="_vote",
        aggregate_function="first",
    )
    prop_cols = [c for c in matrix.columns if c != "intressent_id"]
    if prop_cols:
        matrix = matrix.with_columns(
            [pl.col(c).cast(pl.Float32).fill_null(math.nan) for c in prop_cols]
        )

    member_stats = filtered.group_by("intressent_id").agg(
        pl.col("namn").sort_by("datum").last(),
        pl.col("parti").sort_by("datum").last(),
        pl.col("kon").sort_by("datum").last(),
        pl.col("fodd_ar").sort_by("datum").last(),
        (~pl.col("_vote").is_nan()).sum().cast(pl.Int32).alias("vote_count"),
    )

    metadata = member_stats.with_columns(
        (pl.col("vote_count") < min_votes).alias("low_confidence")
    ).select(
        [
            "intressent_id",
            "namn",
            "parti",
            "kon",
            "fodd_ar",
            "vote_count",
            "low_confidence",
        ]
    )

    matrix = matrix.sort("intressent_id")
    metadata = metadata.sort("intressent_id")

    return matrix, metadata
