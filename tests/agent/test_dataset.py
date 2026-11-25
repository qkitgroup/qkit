from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from qkit.agent import data_access as da
from qkit.agent import entrypoint


@pytest.fixture(scope="session", autouse=True)
def setup():
    import os
    import pathlib

    from qkit.install.install import create_base_structure

    cwd = pathlib.Path(os.getcwd())
    create_base_structure(cwd)


@pytest.fixture()
def h5_file(tmp_path):
    """A small measurement-like HDF5 file with vectors, a matrix, text and
    complex datasets."""
    fname = tmp_path / "meas.h5"
    with h5py.File(fname, "w") as f:
        grp = f.create_group("data")
        freq = grp.create_dataset("frequency", data=np.linspace(5.9e9, 6.1e9, 1001))
        freq.attrs["unit"] = "Hz"
        signal = 3.0 + 0.5 * np.sin(np.linspace(0, 10, 1001))
        sig = grp.create_dataset("signal", data=signal)
        sig.attrs["unit"] = "a.u."
        sig.attrs["x_ds_url"] = "/data/frequency"
        sig.attrs["comment"] = "test signal"
        grp.create_dataset("scalar", data=np.float64(42.0))
        grp.create_dataset("times", data=np.arange(10000, dtype=np.float64))
        mat = np.arange(20 * 7, dtype=float).reshape(20, 7)
        mat_ds = grp.create_dataset("matrix", data=mat)
        mat_ds.attrs["x_ds_url"] = "/data/rows"
        mat_ds.attrs["y_ds_url"] = "/data/cols"
        grp.create_dataset("rows", data=np.arange(20.0))
        grp.create_dataset("cols", data=np.linspace(-10, 10, 7))
        grp.create_dataset("txt", data=np.array([b"hello agent"]))
        grp.create_dataset(
            "measurement", data=np.array(['{"a": 1, "b": [1, 2]}'], dtype=object)
        )
        grp.create_dataset("complex_ds", data=np.array([1 + 2j, 3 - 1j, -2 + 0.5j]))
    return fname


# --------------------------------------------------------------------------
# baseline correction / normalization / statistics
# --------------------------------------------------------------------------

def test_baseline_correct_scalar_offset_methods():
    y = np.array([5.0, 6.0, 7.0, 8.0])
    np.testing.assert_allclose(da.baseline_correct(y, "first"), [0, 1, 2, 3])
    np.testing.assert_allclose(da.baseline_correct(y, "min"), [0, 1, 2, 3])
    np.testing.assert_allclose(da.baseline_correct(y, "median"), [5 - 6.5, 6 - 6.5, 7 - 6.5, 8 - 6.5])
    np.testing.assert_allclose(da.baseline_correct(y, "none"), y)


def test_baseline_correct_per_trace():
    m = np.array([[0.0, 10.0], [100.0, 20.0]])
    r = da.baseline_correct(m, "first")
    np.testing.assert_allclose(r, [[0.0, 10.0], [0.0, -80.0]])


def test_baseline_correct_invalid():
    with pytest.raises(ValueError):
        da.baseline_correct(np.array([1.0, 2.0]), "bogus")


def test_baseline_als_linear():
    t = np.linspace(0, 1, 101)
    y = 50.0 + 20.0 * t + 0.1 * np.sin(50 * t)
    corrected = y - da.baseline_als(y, lam=1e5, p=0.01, niter=15)
    assert np.allclose(corrected, 0.0, atol=0.5)
    # a straight line is reproduced exactly (second differences vanish)
    y2 = 5.0 + 3.0 * t
    np.testing.assert_allclose(y2 - da.baseline_als(y2), 0.0, atol=1e-3)


def test_baseline_als_nan():
    y = np.array([3.0, 4.0, 5.0, np.nan, 5.0, 6.0])
    base = da.baseline_als(y)
    assert np.isnan(base[3]) and np.all(np.isfinite(base[[0, 1, 2, 4, 5]]))


def test_normalize():
    x = np.array([2.0, 4.0, 10.0])
    np.testing.assert_allclose(da.normalize(x, "minmax"), [0.0, 0.25, 1.0])
    z = da.normalize(x, "zscore")
    assert abs(z.mean()) < 1e-12 and abs(z.std() - 1.0) < 1e-12
    np.testing.assert_array_equal(da.normalize(np.array([5.0, 5.0]), "minmax"), np.zeros(2))
    np.testing.assert_allclose(da.normalize(x, "none"), x)
    with pytest.raises(ValueError):
        da.normalize(x, "bogus")
    xnan = np.array([1.0, 2.0, np.nan])
    r = da.normalize(xnan, "minmax")
    assert np.isnan(r[2]) and r[0] == 0.0 and r[1] == 1.0


# --------------------------------------------------------------------------
# MCP entrypoint
# --------------------------------------------------------------------------

def test_dataset_overview_processing(h5_file, monkeypatch):
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"test-uuid": str(h5_file)})
    )
    res = entrypoint.dataset_overview("test-uuid", "/data/signal", baseline="first")
    expected = 3.0 + 0.5 * np.sin(np.linspace(0, 10, 1001))
    np.testing.assert_allclose(res, expected - expected[0])

    res = entrypoint.dataset_overview("test-uuid", "/data/signal", normalize="minmax")
    assert res.min() == pytest.approx(0.0)
    assert res.max() == pytest.approx(1.0)


def test_dataset_overview_invalid_options(h5_file, monkeypatch):
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"test-uuid": str(h5_file)})
    )
    with pytest.raises(ValueError, match="baseline"):
        entrypoint.dataset_overview("test-uuid", "/data/signal", baseline="bogus")
    with pytest.raises(ValueError, match="normalize"):
        entrypoint.dataset_overview("test-uuid", "/data/signal", normalize="bogus")


def test_dataset_detail_region(h5_file, monkeypatch):
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"test-uuid": str(h5_file)})
    )
    res = entrypoint.dataset_detail("test-uuid", "/data/matrix", region=((0, 9), (0, 6)))
    expected = np.arange(140.0).reshape(20, 7)[:10, :]
    np.testing.assert_array_equal(res, expected)


def test_dataset_detail_processing(h5_file, monkeypatch):
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"test-uuid": str(h5_file)})
    )
    res = entrypoint.dataset_detail(
        "test-uuid",
        "/data/matrix",
        region=((0, 19), (0, 6)),
        baseline="first",
        normalize="minmax",
    )
    assert res.shape == (20, 7)
    assert res.min() == pytest.approx(0.0)
    assert res.max() == pytest.approx(1.0)


def test_dataset_detail_trailing_singleton(tmp_path, monkeypatch):
    fname = tmp_path / "mat3d.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("mat", data=np.arange(24.0).reshape(4, 6, 1))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"u": str(fname)})
    )
    res = entrypoint.dataset_detail("u", "/mat", region=((0, 3), (0, 5), (0, 0)), baseline="first")
    expected = np.arange(24.0).reshape(4, 6, 1)[..., 0]
    assert res.shape == (4, 6)
    np.testing.assert_allclose(res, expected - expected[..., :1])


def test_dataset_detail_bounded(tmp_path, monkeypatch):
    fname = tmp_path / "big.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("mat", data=np.arange(200 * 200.0).reshape(200, 200))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"u": str(fname)})
    )
    res = entrypoint.dataset_detail(
        "u", "/mat", region=((0, 199), (0, 199)), max_points=1000
    )
    assert res.size <= 1000


def test_dataset_detail_invalid_region(tmp_path, monkeypatch):
    fname = tmp_path / "small.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("mat", data=np.zeros((4, 6)))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"u": str(fname)})
    )
    with pytest.raises(ValueError, match="axes"):
        entrypoint.dataset_detail("u", "/mat", region=((0, 5),))
    with pytest.raises(ValueError, match="outside"):
        entrypoint.dataset_detail("u", "/mat", region=((0, 4), (0, 6)))


# --------------------------------------------------------------------------
# block averaging downsample
# --------------------------------------------------------------------------

def test_downsample_average_1d():
    x = np.arange(100.0)
    r = da.downsample_average(x, 10)
    assert r.shape == (10,)
    np.testing.assert_allclose(r, x.reshape(10, 10).mean(axis=1))
    # a 1D reduction by `factor` keeps at most ceil(n / factor) samples
    assert len(da.downsample_average(np.arange(201.0), 2)) <= 101
    # factor 1 and scalars are passed through
    np.testing.assert_array_equal(da.downsample_average(x, 1), x)
    np.testing.assert_array_equal(da.downsample_average(np.float64(3.0), 5), np.float64(3.0))


def test_downsample_average_2d():
    x = np.arange(20 * 8, dtype=float).reshape(20, 8)
    # factor 4 -> 2x2 blocks (sqrt(4) per axis)
    r = da.downsample_average(x, 4)
    assert r.shape == (10, 4)
    expected = x.reshape(10, 2, 4, 2).mean(axis=(1, 3))
    np.testing.assert_allclose(r, expected)


def test_downsample_average_nan():
    x = np.array([1.0, 3.0, np.nan, 5.0])
    np.testing.assert_allclose(da.downsample_average(x, 2), [2.0, 5.0])
    # a block without usable samples becomes NaN
    r = da.downsample_average(np.array([np.nan, np.nan, 1.0, 1.0]), 2)
    assert np.isnan(r[0]) and r[1] == 1.0


def test_downsample_average_complex():
    x = np.array([1.0 + 2j, 3.0 - 1j, -2.0 + 0.5j, 4.0 + 0j])
    r = da.downsample_average(x, 2)
    expected = np.array([(1.0 + 2j + 3.0 - 1j) / 2, (-2.0 + 0.5j + 4.0) / 2])
    np.testing.assert_allclose(r, expected)


def test_downsample_average_max_points():
    x = np.arange(100.0).reshape(10, 10)
    r = da.downsample_average(x, 2, max_points=5)
    assert r.size <= 5
    assert r.shape == (2, 2)
    # the top-left output sample is the mean of the corresponding block
    assert r[0, 0] == pytest.approx(x[:5, :5].mean())


def test_dataset_overview_small(h5_file, monkeypatch):
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"test-uuid": str(h5_file)})
    )
    res = entrypoint.dataset_overview("test-uuid", "/data/signal")
    with h5py.File(h5_file, "r") as f:
        np.testing.assert_array_equal(res, f["/data/signal"][:])


def test_dataset_overview_1d_downsampled(tmp_path, monkeypatch):
    fname = tmp_path / "big.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("big", data=np.arange(100000.0))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"big-uuid": str(fname)})
    )
    res = entrypoint.dataset_overview("big-uuid", "/big")
    assert isinstance(res, np.ndarray)
    # scale_factor = ceil(100000 / 20000) = 5 -> 20000 averaged samples
    assert res.shape == (20000,)
    np.testing.assert_allclose(res[:2], [2.0, 7.0])


def test_dataset_overview_2d_downsampled(tmp_path, monkeypatch):
    fname = tmp_path / "big2d.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("mat", data=np.arange(200 * 300.0).reshape(200, 300))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"u2": str(fname)})
    )
    res = entrypoint.dataset_overview("u2", "/mat")
    assert res.shape == (100, 150)
    # top-left output sample averages the top-left 2x2 input block
    expected = np.arange(60000.0).reshape(200, 300)[:2, :2].mean()
    assert res[0, 0] == pytest.approx(expected)


def test_dataset_overview_text_downsampled(tmp_path, monkeypatch):
    fname = tmp_path / "bigtxt.h5"
    with h5py.File(fname, "w") as f:
        f.create_dataset("txt", data=np.array([b"x"] * 30000, dtype="S1"))
    monkeypatch.setitem(
        entrypoint.qkit.__dict__, "fid", SimpleNamespace(h5_db={"t": str(fname)})
    )
    res = entrypoint.dataset_overview("t", "/txt")
    assert isinstance(res, np.ndarray)
    assert res.size <= 20000


def test_read_view(h5_file):
    with h5py.File(h5_file, "r") as f:
        signal = 3.0 + 0.5 * np.sin(np.linspace(0, 10, 1001))
        # small views pass through unchanged
        np.testing.assert_array_equal(da.read_view(f["/data/signal"], max_points=2000), signal)
        # oversized views are bounded to max_points
        assert da.read_view(f["/data/times"], max_points=100).size <= 100
        assert da.read_view(f["/data/matrix"], max_points=30).size <= 30
        assert da.read_view(f["/data/txt"], max_points=1).size <= 1
        # a selection restricts the read before decimation
        sel = da.read_view(
            f["/data/matrix"], max_points=100, selection=(slice(0, 5), slice(0, 3))
        )
        np.testing.assert_array_equal(sel, np.arange(140.0).reshape(20, 7)[:5, :3])
        # baseline/normalize are forwarded to process_view
        proc = da.read_view(
            f["/data/signal"], max_points=2000, baseline="first", normalize_method="minmax"
        )
        assert proc.min() == pytest.approx(0.0)
        assert proc.max() == pytest.approx(1.0)
