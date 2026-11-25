import logging
import os

from mcp.server import MCPServer

import qkit
from qkit.agent.auth import StaticTokenVerifier
from qkit.agent.data_access import dtype_string, read_view
from qkit.storage.store import Data

log = logging.getLogger(__name__)

SERVER_URL = "http://localhost:8000"

#: A view returned by the dataset read tools never exceeds this many values.
MAX_VIEW_POINTS = 20_000

server = MCPServer(
    name="qkit",
    token_verifier=StaticTokenVerifier(),
    auth=StaticTokenVerifier.create_auth_settings(SERVER_URL),
    description="Qkit MCP server - Read, Execute Experiments on real hardware",
    instructions="Consult this MCP server if you need to evaluate or execute quantum experiments on real hardware"
)

@server.tool()
def list_devices() -> list[str]:
    """
    List available measurement devices. Useful when trying to determine which experiments can be run.
    """
    return qkit.instruments.get_instrument_names()

@server.tool()
def list_measurements(offset: int = 0, limit: int = 10) -> list[str]:
    """
    List all measurements stored in the database by its UUID, from newest to oldest.
    """
    return list(qkit.fid.h5_db.keys())[offset:offset+limit]

def _open_uuid(uuid: str):
    file = qkit.fid.h5_db[uuid]
    if not file:
        raise ValueError(f"Measurement with UUID {uuid} not found")
    return Data(file)

def _open_dataset(uuid: str, dataset_name: str):
    """Return the dataset (by name) of a measurement (identified by its UUID)."""
    return _open_uuid(uuid).hf.hf[dataset_name]

@server.tool()
def list_datasets(uuid: str) -> list[str]:
    """
    List all datasets by name of a measurement (identified by its UUID).
    """
    h5 = _open_uuid(uuid).hf.hf
    dataset_list = []
    h5.visititems(lambda name, item: dataset_list.append(name))
    return dataset_list

@server.tool()
def dataset_metadata(uuid: str, dataset_name: str):
    """
    Get metadata about a particular dataset (by name) of a given measurement (by UUID).
    """
    ds = _open_dataset(uuid, dataset_name)
    return {
        "datatype": dtype_string(ds.dtype),
        "dimensions": list(ds.shape),
        "attributes": dict(ds.attrs),
    }

def _region_to_slices(
    region: tuple[tuple[int, int], ...], shape
) -> tuple[slice, ...]:
    """Convert per-axis inclusive (start, end) region pairs to slices."""
    if len(region) != len(shape):
        raise ValueError(
            f"region must contain one (start, end) pair per axis: dataset has "
            f"{len(shape)} axes, got {len(region)}"
        )
    slices = []
    for (start, end), size in zip(region, shape):
        if start < 0 or end < start or end >= size:
            raise ValueError(f"region ({start}, {end}) is outside axis of length {size}")
        slices.append(slice(start, end + 1))
    return tuple(slices)

@server.tool()
def dataset_overview(
    uuid: str,
    dataset_name: str,
    baseline: str = "none",
    normalize: str = "none",
):
    """
    Provides a down-sampled overview of a dataset (by name) of a given measurement (by UUID).

    Datasets with more than ``max_points`` values are reduced by block
    averaging (strided decimation for text datasets). Optionally a per-trace
    ``baseline`` (none, first, min, median, als) is subtracted and the view
    globally ``normalize``d (none, minmax, zscore) so that slow measurement
    artifacts (e.g. readout-line background) do not hide the signal.
    """
    ds = _open_dataset(uuid, dataset_name)
    return read_view(
        ds, max_points=MAX_VIEW_POINTS, baseline=baseline, normalize_method=normalize
    )


@server.tool()
def dataset_detail(
    uuid: str,
    dataset_name: str,
    region: tuple[tuple[int, int], ...],
    scale_factor: int = 1,
    max_points: int = MAX_VIEW_POINTS,
    baseline: str = "none",
    normalize: str = "none",
):
    """
    Provides a detailed view of a dataset (by name) of a given measurement (by UUID), with a specified region.

    ``region`` selects one inclusive (start, end) pair per axis of the
    dataset; the returned view never exceeds ``max_points`` values.
    Optionally a per-trace ``baseline`` (none, first, min, median, als) is
    subtracted and the view globally ``normalize``d (none, minmax, zscore)
    so that slow measurement artifacts (e.g. readout-line background) do not
    hide the signal.
    """
    ds = _open_dataset(uuid, dataset_name)
    selection = _region_to_slices(region, ds.shape)
    return read_view(
        ds,
        max_points=max_points,
        scale_factor=scale_factor,
        selection=selection,
        baseline=baseline,
        normalize_method=normalize,
    )

def mcp_main():
    server.run(transport="streamable-http", host="localhost", port=8000)


if __name__ == "__main__":
    qkit.start()
    if StaticTokenVerifier.MCP_TOKEN_KEY not in qkit.cfg:
        log.info(f"Setting {StaticTokenVerifier.MCP_TOKEN_KEY} from environment")
        qkit.cfg[StaticTokenVerifier.MCP_TOKEN_KEY] = os.environ[StaticTokenVerifier.MCP_TOKEN_KEY.upper()]
    mcp_main()