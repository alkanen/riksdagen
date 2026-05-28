"""Train a hexagonal Kohonen SOM on the member × proposition vote matrix.

Library choice: minisom (pure Python/NumPy) over somoclu (C++ backend).
minisom ships with hexagonal topology support and accepts a callable
activation_distance, making it straightforward to plug in NaN-aware cosine
distance without subclassing. somoclu's C++ build adds complexity on WSL2 with
no meaningful speed advantage at the data sizes this pipeline handles.

Distance metric: cosine distance computed only over dimensions where the input
vector is non-NaN (i.e. the member actually cast a vote). Weight vectors are
always dense, so the mask is derived from the input side only.

NaN and weight updates: the activation distance (BMU selection) uses the full
NaN-masked cosine metric. The weight-update step updates only the dimensions
where the member actually voted (non-NaN); absent-vote dimensions are left
completely untouched so they carry no spurious signal.
"""

from __future__ import annotations

from collections.abc import Callable, Collection

import numpy as np
import numpy.typing as npt
import polars as pl
from minisom import MiniSom
from tqdm import tqdm

from riksdagen.config import Config


def _nan_cosine_distance(
    x: npt.NDArray[np.float64],
    weights: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """Cosine distance between x and each weight vector over non-NaN dims of x.

    Args:
        x:       Input vector of shape (input_len,).  May contain NaN.
        weights: SOM weight cube of shape (grid_x, grid_y, input_len).

    Returns:
        Distance map of shape (grid_x, grid_y) in [0, 2].
    """
    mask: npt.NDArray[np.bool_] = ~np.isnan(x)
    if not mask.any():
        return np.ones(weights.shape[:2], dtype=np.float64)
    w: npt.NDArray[np.float64] = weights[..., mask]  # (grid_x, grid_y, n_shared)
    v: npt.NDArray[np.float64] = x[mask]  # (n_shared,)
    dot: npt.NDArray[np.float64] = np.einsum("...i,i->...", w, v)
    w_norm: npt.NDArray[np.float64] = np.linalg.norm(w, axis=-1)
    v_norm = float(np.linalg.norm(v))
    denom: npt.NDArray[np.float64] = w_norm * v_norm
    sim: npt.NDArray[np.float64] = np.where(denom > 0.0, dot / denom, 0.0)
    return (1.0 - sim).astype(np.float64)


def _assignments(
    som: MiniSom, vectors: npt.NDArray[np.float64], ids: list[str]
) -> pl.DataFrame:
    grid_x: list[int] = []
    grid_y: list[int] = []
    for v in vectors:
        wx, wy = som.winner(v)
        grid_x.append(int(wx))
        grid_y.append(int(wy))
    return pl.DataFrame(
        {
            "intressent_id": ids,
            "grid_x": pl.Series(grid_x, dtype=pl.Int32),
            "grid_y": pl.Series(grid_y, dtype=pl.Int32),
        }
    )


def train_som(
    matrix: pl.DataFrame,
    config: Config,
    *,
    seed: int = 42,
    n_epochs: int = 10,
    learning_rate: float = 0.5,
    sigma: float | None = None,
    lr_decay: str = "asymptotic_decay",
    sigma_decay: str = "linear_decay_to_one",
    pca_init: bool = True,
    snapshot_at: Collection[int] = (),
    on_snapshot: Callable[[int, pl.DataFrame], None] | None = None,
) -> tuple[pl.DataFrame, npt.NDArray[np.float64]]:
    """Train a hexagonal SOM and return per-member grid-cell assignments and weights.

    Args:
        matrix:        Output of build_vote_matrix — intressent_id column +
                       Float32 proposition columns.  NaN encodes Frånvaro.
        config:        Pipeline config supplying grid_width and grid_height.
        seed:          RNG seed for reproducible weight initialisation and
                       epoch shuffling.
        n_epochs:      Number of full passes over the data.  More epochs spread
                       the asymptotic learning-rate decay over more steps,
                       giving the topology more time to form before the rate
                       drops toward zero.
        learning_rate: Initial learning rate.  Lower values produce gentler,
                       more gradual convergence.
        sigma:         Initial neighbourhood radius (Gaussian σ).  Defaults to
                       half the longer grid dimension.  Larger values spread
                       influence further across the grid during early training.
        lr_decay:      Decay schedule for the learning rate.  One of:
                         'asymptotic_decay'   — decays to ⅓ of initial value
                         'linear_decay_to_zero' — reaches 0 at end of training
                         'inverse_decay_to_zero' — faster asymptotic drop to 0
        sigma_decay:   Decay schedule for σ.  One of:
                         'linear_decay_to_one'  — (default) uniform shrink to 1,
                                                  keeps neighbourhood wide for
                                                  longer to help spread clusters
                         'asymptotic_decay'     — decays to ⅓ of initial value
                         'inverse_decay_to_one' — fast initial drop then slow
        pca_init:      If True (default), initialise grid weights along the
                       first two principal components of the vote data so that
                       members start spread across the grid rather than
                       collapsing to a few random attractors from epoch 1.
                       NaN values are imputed to 0 for PCA only.
        snapshot_at:   1-indexed epoch numbers after which on_snapshot is called.
        on_snapshot:   Callback invoked as on_snapshot(epoch, assignments) for
                       each epoch in snapshot_at.  Runs inside the tqdm loop so
                       the progress bar stays on screen.

    Returns:
        (assignments, weights) where:
            assignments  DataFrame with intressent_id, grid_x, grid_y — one row
                         per member in the same order as the input matrix.
            weights      float64 array of shape (grid_width, grid_height, n_dims)
                         — the final SOM weight cube, one vector per grid cell.
    """
    ids: list[str] = matrix["intressent_id"].to_list()
    prop_cols = [c for c in matrix.columns if c != "intressent_id"]

    if not prop_cols:
        n = len(ids)
        empty_assignments = pl.DataFrame(
            {
                "intressent_id": ids,
                "grid_x": pl.Series([0] * n, dtype=pl.Int32),
                "grid_y": pl.Series([0] * n, dtype=pl.Int32),
            }
        )
        empty_weights: npt.NDArray[np.float64] = np.empty(
            (config.grid_width, config.grid_height, 0), dtype=np.float64
        )
        return empty_assignments, empty_weights

    vectors: npt.NDArray[np.float64] = (
        matrix.select(prop_cols).to_numpy().astype(np.float64)
    )
    n_members, n_dims = vectors.shape

    _sigma = (
        sigma if sigma is not None else max(config.grid_width, config.grid_height) / 2.0
    )
    som: MiniSom = MiniSom(
        config.grid_width,
        config.grid_height,
        n_dims,
        sigma=_sigma,
        learning_rate=learning_rate,
        decay_function=lr_decay,
        sigma_decay_function=sigma_decay,
        topology="hexagonal",
        neighborhood_function="gaussian",
        activation_distance=_nan_cosine_distance,
        random_seed=seed,
    )

    if pca_init:
        vectors_imputed: npt.NDArray[np.float64] = np.where(
            np.isnan(vectors), 0.0, vectors
        )
        som.pca_weights_init(vectors_imputed)

    rng = np.random.default_rng(seed)
    n_iters = n_epochs * n_members
    _snapshot_at = frozenset(snapshot_at)

    for epoch in tqdm(range(n_epochs), desc="Training SOM", unit="epoch"):
        order: npt.NDArray[np.intp] = rng.permutation(n_members)
        for local_t, idx in enumerate(order):
            v: npt.NDArray[np.float64] = vectors[idx]
            vote_mask: npt.NDArray[np.bool_] = ~np.isnan(v)
            win = som.winner(v)
            t = epoch * n_members + local_t
            if vote_mask.any():
                eta = som._learning_rate_decay_function(som._learning_rate, t, n_iters)
                sig = som._sigma_decay_function(som._sigma, t, n_iters)
                g: npt.NDArray[np.float64] = som.neighborhood(win, sig) * eta
                som._weights[..., vote_mask] += np.einsum(
                    "ij, ijk->ijk",
                    g,
                    v[vote_mask] - som._weights[..., vote_mask],
                )
        epoch_num = epoch + 1
        if on_snapshot is not None and epoch_num in _snapshot_at:
            on_snapshot(epoch_num, _assignments(som, vectors, ids))

    return _assignments(som, vectors, ids), np.array(som._weights, dtype=np.float64)
