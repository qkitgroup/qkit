"""
This python file attempts to solve the problem of multiple machine beeing backed up to a different path, and the user still
having to find .h5-Files using a UUID.

While a human user can use intuition to find the file, even guided search fails to efficiently find UUID.h5 files. Here, a
file based protocol is used to create hints for the search algorithm:

When a machine has created its file info database, it is written to disk. It contains a mapping from the UUID to a path relative
to the breadcrumb file. As a machine only sees its own files, and not the ones created by other machines, each machine must
create a list of files it knows, at a location not colliding with the files of others.

Here, we implement a file at `.{Node-UUID}.breadcrumb` derived fromt the MAC-Address.

The file contents are untrusted. (Who knows where they come from.) They thus may not be pickled. The following format is used:
UUID=rel_path\n

The UUID is 6 symbols long. It is followed by an `=` symbol. The rest of the line is the relative path.
"""

from pathlib import Path
import qkit
import os
import itertools

FILE_END = ".breadcrumb"

def derive_breadcrumb_filename() -> Path:
    """
    Derive a machine-unique breadcrumb file name in the data-directory.
    """
    import uuid
    node = uuid.getnode()
    filename = f".{node:x}{FILE_END}"
    return Path(qkit.cfg['datadir']) / filename

class BreadCrumbCreator():
    """
    Manages creating the initial bread crumb file and updating it after each measurement.
    """

    def __init__(self) -> None:
        self._breadcrumb_path = derive_breadcrumb_filename()
        if self._breadcrumb_path.exists():
            os.remove(self._breadcrumb_path)
        self._breadcrumb_file = open(self._breadcrumb_path, mode="w")

    def append_entry(self, uuid: str, path: Path|str):
        rel_path = Path(path).relative_to(self._breadcrumb_path.parent)
        print(f"{uuid[:6]}={rel_path}", file=self._breadcrumb_file, flush=True) # Fails if uuid is not 6 digits

def read_breadcrumb(path: Path) -> dict[str, Path]:
    """
    Read a breadcrumb file.
    """
    breadcrumb_parent = path.parent
    uuid_map: dict[str, Path] = {}
    with open(path, mode="r") as f:
        for line in f.readlines():
            if line[6] == '=': # Valid format
                uuid = line[:6]
                rel_path = line[7:].strip()
                uuid_map[uuid] = breadcrumb_parent / rel_path
    return uuid_map

def read_breadcrumbs(dir: Path) -> dict[str, Path]:
    assert dir.is_dir(), "Directory must be a directory!"
    breadcrumbs = [f for f in dir.iterdir() if f.is_file and f.name.endswith(FILE_END)]
    return dict(itertools.chain.from_iterable(map(dict.items, map(read_breadcrumb, breadcrumbs))))

def manual_index():
    import os
    import qkit

    qkit.cfg['fid_scan_datadir'] = True
    current_dir = os.getcwd()
    print("Current Directory: ", current_dir)
    if input("Index? (y/N)") == "y":
        qkit.cfg['datadir'] = current_dir
        import qkit.core.s_init.S16_available_modules
        from qkit.core.lib.file_service.file_info_database import fid
        fid = fid()

if __name__ == "__main__":
    manual_index()