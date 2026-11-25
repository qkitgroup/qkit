"""Agent-facing access to the data of a qkit measurement.

The MCP tools :func:`qkit.agent.entrypoint.dataset_overview` and
:func:`qkit.agent.entrypoint.dataset_detail` let an agent read the values of
a single dataset of a measurement (optionally baseline-corrected and
normalized); they are thin wrappers around this module, which contains the
pure data pipeline:

    h5py dataset
        -> read (selection) + reduction (bounded output)
        -> optional baseline correction (per innermost trace)
        -> optional normalization
        -> view / metadata

Design goals
------------
* **Bounded output** - the returned view never exceeds ``max_points`` values
  no matter how large the dataset is, so the answer always fits an LLM
  context window.
* **Honest by default** - no processing is applied unless requested; the
  returned view is the raw (optionally processed) values.
* **Baseline shifts and normalization** - traces from different scans or
  settings may sit on different baselines or scales; the ``baseline`` and
  ``normalize`` options make them comparable.
"""

from __future__ import annotations

import math
import warnings
from functools import reduce
from typing import Optional

import h5py
import numpy as np
from scipy import sparse
from scipy.sparse import linalg as splinalg

#: Valid values for the ``baseline`` option of :func:`process_view`.
BASELINE_METHODS = ("none", "first", "min", "median", "als")
#: Valid values for the ``normalize`` option of :func:`process_view`.
NORMALIZE_METHODS = ("none", "minmax", "zscore")

#: Default maximum number of values returned by the read tools.
DEFAULT_MAX_POINTS = 256

__all__ = [
    "BASELINE_METHODS",
    "DEFAULT_MAX_POINTS",
    "NORMALIZE_METHODS",
    "baseline_als",
    "baseline_correct",
    "downsample_average",
    "dtype_string",
    "normalize",
    "process_view",
    "read_view",
]


def dtype_string(dtype) -> str:
    """Return a readable datatype string for an h5py/numpy dtype."""
    try:
        if h5py.check_string_dtype(dtype) is not None:
            return "str"
        vlen_dtype = h5py.check_vlen_dtype(dtype)
        if vlen_dtype is not None:
            return "vlen " + getattr(vlen_dtype, "__name__", str(vlen_dtype))
    except AttributeError:
        pass
    if getattr(dtype, "kind", None) == "O":
        return "object"
    return dtype.name if hasattr(dtype, "name") else str(dtype)


def downsample_average(
        data: np.ndarray,
        factor: int,
        max_points: Optional[int] = None,
) -> np.ndarray:
    """Downsample a numeric array by ``factor`` using block averaging.

    Every output value is the mean of a non-overlapping block of input
    values; the total reduction factor is distributed over the axes, so the
    multi-dimensional layout of the data is preserved. Blocks are aligned to
    the array origin, trailing partial blocks are dropped, and NaN samples
    are ignored per block (a block without usable samples yields NaN).

    If ``max_points`` is given, the per-axis block sizes are increased until
    the result holds at most ``max_points`` values.
    """
    x = np.asarray(data)
    ndim = x.ndim
    factor = max(1, int(factor))
    if ndim == 0 or factor == 1 or x.size == 0:
        return x

    # Distribute the total factor about evenly over the axes (ceil keeps the
    # product >= factor), then grow block sizes while the view stays bounded.
    per_axis = max(1, int(math.ceil(factor ** (1.0 / ndim))))
    blocks = [per_axis] * ndim
    out: list[int] = [int(math.ceil(n / b)) for n, b in zip(x.shape, blocks)]
    if max_points is not None:
        max_points = max(1, int(max_points))
        while reduce(lambda a, b: a * b, out, 1) > max_points:
            axis = int(np.argmax(out))
            blocks[axis] += 1
            out[axis] = int(math.ceil(x.shape[axis] / blocks[axis]))

    # Trim trailing partial blocks and fold the block dimensions in.
    trimmed = tuple(
        slice(0, n - (n % b)) if b > 1 else slice(0, n)
        for n, b in zip(x.shape, blocks)
    )
    y = x[trimmed]
    new_shape: list[int] = []
    block_axes: list[int] = []
    for n, b in zip(y.shape, blocks):
        if b > 1:
            new_shape.extend([n // b, b])
            block_axes.append(len(new_shape) - 1)
        else:
            new_shape.append(n)
    y = y.reshape(new_shape)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(y, axis=tuple(block_axes))


def baseline_als(y: np.ndarray, lam: float = 1e5, p: float = 0.01, niter: int = 10) -> np.ndarray:
    """Asymmetric least-squares smooth baseline (Eilers & Boelens 2005).

    Fits a baseline that follows the lower envelope of the 1D trace ``y``
    (``p`` weighs points below the fit more heavily). Non-finite samples are
    filled with the finite median for the fit and stay non-finite in the
    result. Requires at least three points.
    """
    y = np.asarray(y, dtype=float)
    n = y.size
    if n < 3:
        return np.where(np.isfinite(y), y, 0.0).copy()
    finite = y[np.isfinite(y)]
    fill = float(np.median(finite)) if finite.size else 0.0
    yf = np.where(np.isfinite(y), y, fill)
    d = sparse.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    penalty = d.T @ d
    z = yf.copy()
    for _ in range(niter):
        w = p * (yf > z) + (1.0 - p) * (yf < z)
        wsp = sparse.diags(w, 0, shape=(n, n))
        z = splinalg.spsolve((wsp + lam * penalty).tocsc(), w * yf)
    return np.where(np.isfinite(y), z, np.nan)


def _als_correct(data: np.ndarray, lam: float = 1e5, p: float = 0.01, niter: int = 10) -> np.ndarray:
    """Subtract an ALS baseline from every innermost trace of `data`."""
    x = np.asarray(data, dtype=float)
    flat = x.reshape(-1, x.shape[-1])
    out = np.empty_like(flat)
    for i, trace in enumerate(flat):
        finite = trace[np.isfinite(trace)]
        if trace.size < 3 or finite.size < 3:
            offset = float(np.mean(finite)) if finite.size else 0.0
            out[i] = trace - offset
            continue
        out[i] = trace - baseline_als(trace, lam=lam, p=p, niter=niter)
    return out.reshape(x.shape)


def baseline_correct(data, method: str = "none"):
    """Subtract a baseline from a numeric array, per innermost trace.

    ``method`` may be:

    * ``"none"`` - return the data unchanged
    * ``"first"`` - subtract the first sample of every trace
    * ``"min"`` - subtract the minimum of every trace (shifts data >= 0)
    * ``"median"`` - subtract the median (robust central offset)
    * ``"als"`` - subtract a smooth asymmetric-least-squares baseline
      (:func:`baseline_als`) fitted to every trace (drift/curvature)

    For arrays with more than one dimension the correction is applied along the
    last (innermost) axis, i.e. per trace, which matches how qkit writes matrix
    data (rows = outer axis). Complex arrays are corrected per component.
    """
    if method in (None, "", "none"):
        return data
    if method not in BASELINE_METHODS:
        raise ValueError(f"baseline must be one of {BASELINE_METHODS}, got {method!r}")
    x = np.asarray(data)
    if np.iscomplexobj(x):
        return baseline_correct(x.real, method) + 1j * baseline_correct(x.imag, method)
    if x.size == 0:
        return x
    if method == "first":
        return x - x[..., :1]
    if method == "min":
        return x - np.nanmin(x, axis=-1, keepdims=True)
    if method == "median":
        return x - np.nanmedian(x, axis=-1, keepdims=True)
    if method == "als":
        return _als_correct(x)
    raise AssertionError(f"unreachable: method {method!r}")


def normalize(data, method: str = "none"):
    """Normalize a numeric array.

    ``method`` may be:

    * ``"none"`` - return the data unchanged
    * ``"minmax"`` - scale globally so min -> 0 and max -> 1
    * ``"zscore"`` - zero mean, unit variance

    Constant arrays produce zeros. Normalization is global, not per trace;
    combine with :func:`baseline_correct` for per-trace offsets. Complex arrays
    are normalized per component.
    """
    if method in (None, "", "none"):
        return data
    if method not in NORMALIZE_METHODS:
        raise ValueError(f"normalize must be one of {NORMALIZE_METHODS}, got {method!r}")
    x = np.asarray(data)
    if np.iscomplexobj(x):
        return normalize(x.real, method) + 1j * normalize(x.imag, method)
    if x.size == 0:
        return x
    finite = x[np.isfinite(x)]
    if finite.size == 0:
        return x
    if method == "minmax":
        lo, hi = float(finite.min()), float(finite.max())
        span = hi - lo
        if span == 0:
            return np.zeros_like(x, dtype=float)
        return (x - lo) / span
    if method == "zscore":
        mu, sd = float(finite.mean()), float(finite.std())
        if sd == 0:
            return np.zeros_like(x, dtype=float)
        return (x - mu) / sd
    raise AssertionError(f"unreachable: method {method!r}")


def _squeeze_trailing_axes(data: np.ndarray) -> np.ndarray:
    """Drop trailing size-1 axes of a numeric array.

    qkit sometimes writes matrix data with a trailing singleton dimension
    (e.g. ``(x, y, 1)`` for a 2D scan with a z-lookup). Per-innermost-trace
    operations such as baseline correction would then act on a length-1
    "trace", which is meaningless; the dummy axis is removed first.
    """
    x = np.asarray(data)
    while x.ndim > 1 and x.shape[-1] == 1:
        x = x.reshape(x.shape[:-1])
    return x


def process_view(data, baseline: str = "none", normalize_method: str = "none"):
    """Apply optional baseline correction and normalization to a raw view.

    Used by the MCP read tools (``dataset_overview`` / ``dataset_detail``):
    the input is a (possibly decimated) slice straight from the file, the
    output is the same view with per-innermost-trace ``baseline`` correction
    (none|first|min|median|als) and global normalization (none|minmax|zscore)
    applied. Trailing size-1 axes are dropped first so that qkit's
    ``(x, y, 1)`` layout is treated as ``(x, y)``; scalar views are reshaped
    to one point. Text/object data is returned unchanged. Invalid method
    names raise ``ValueError``.
    """
    baseline = baseline or "none"
    normalize_method = normalize_method or "none"
    if baseline not in BASELINE_METHODS:
        raise ValueError(f"baseline must be one of {BASELINE_METHODS}, got {baseline!r}")
    if normalize_method not in NORMALIZE_METHODS:
        raise ValueError(f"normalize must be one of {NORMALIZE_METHODS}, got {normalize_method!r}")
    x = np.asarray(data)
    if x.dtype.kind not in "biufc":
        return data
    if baseline == "none" and normalize_method == "none":
        return data
    x = _squeeze_trailing_axes(x)
    if x.ndim == 0:
        x = x.reshape(1)
    x = baseline_correct(x, baseline)
    return normalize(x, normalize_method)


def _decimate_text(data: np.ndarray, max_points: int) -> np.ndarray:
    """Uniformly strided-decimate a text/object array to <= max_points values.

    Text/object datasets cannot be block-averaged (:func:`downsample_average`);
    they are reduced by taking every n-th sample per axis instead. Scalar and
    already-small views are returned unchanged.
    """
    x = np.asarray(data)
    if x.ndim == 0 or x.size <= max_points:
        return x
    target = max(1, int(round(max_points ** (1.0 / x.ndim))))
    step = tuple(max(1, math.ceil(n / min(target, n))) for n in x.shape)
    return x[tuple(slice(0, n, s) for n, s in zip(x.shape, step))]


def read_view(
        ds: h5py.Dataset,
        max_points: int = DEFAULT_MAX_POINTS,
        scale_factor: int = 1,
        selection: Optional[tuple[slice, ...]] = None,
        baseline: str = "none",
        normalize_method: str = "none",
) -> np.ndarray:
    """Read a dataset, bounded to at most ``max_points`` values, and process it.

    Shared read path behind the MCP tools ``dataset_overview`` and
    ``dataset_detail``: reads the whole dataset (or only the region given by
    ``selection``) and reduces it so the view holds at most ``max_points``
    values - numeric arrays by block averaging (:func:`downsample_average`),
    text/object arrays by uniform strided decimation. A caller-requested
    minimum ``scale_factor`` is respected and raised automatically when the
    bound requires it. The reduced view is then passed through
    :func:`process_view` for optional per-trace ``baseline`` correction and
    global normalization, so the tools only forward ``baseline``/``normalize``.
    """
    max_points = max(1, int(max_points))
    data = np.asarray(ds[:] if selection is None else ds[selection])
    total = data.size
    if data.dtype.kind in "biufc":
        if total > max_points:
            scale_factor = max(int(scale_factor), math.ceil(total / max(1, max_points)))
        data = downsample_average(data, scale_factor, max_points=max_points)
    elif total > max_points:
        data = _decimate_text(data, max_points)
    return process_view(data, baseline=baseline, normalize_method=normalize_method)
