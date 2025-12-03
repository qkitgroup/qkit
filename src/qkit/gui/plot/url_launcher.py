"""
Launch qviewkit based on a provided URL.
This code is independent of qviewkit and does not directly interface with it.
It launches qviewkit as a sub-process (same as plot.py).
An URL is formated as follows:

qviewkit://<UUID>?arg=param&...
"""
import sys
from pathlib import Path

import qkit
from qkit.core.lib.file_service import breadcrumbs
from qkit.gui.qviewkit.main import main

try:
    from parsita import *
    from parsita.util import constant
except ImportError:
    raise ImportError("Please install parsita to use the Qviewkit URL parser (i.e. install qkit with the url option).")
from typing import Tuple, Optional


class QviewkitURLParser(ParserContext):
    """
    Parses a qviewkit url into its components. It consists out of a prefix, and a UUID.

    The UUID may be optionally followed by a `?`, and a `&` separated `key=value` list.
    """

    HINT_ARGUMENT = "hint"

    _prefix = lit('qviewkit://')
    _argument_name = reg(r'[a-zA-Z\-_]+')
    _argument_value = reg(r'[^&]+')
    _kv = _argument_name << lit('=') & _argument_value
    _arguments = (lit('?') >> rep1sep(_kv, lit('&')) << eof > dict) | (eof > constant({}))
    _uuid = reg(r'[A-Z0-9]{6}') > str
    url_pattern = _prefix >> _uuid << opt(lit('/')) & _arguments

    @classmethod
    def parse(cls, data) -> Tuple[str, Optional[dict]]:
        """
        Parses a qviewkit URL into a UUID and a dict containing optional arguments.
        """
        result = cls.url_pattern.parse(data)
        assert isinstance(result, Success), f"Parsing unsuccessful! URL: {data}"
        unwrapped = result.unwrap()
        return unwrapped

def url_handler(args=sys.argv):
    """
    Launch a qviewkit window with the file specified by the url.

    Takes as its only argument the qviewkit-url of the form `qviewkit://ABCDEF`, where `ABCDEF` is the UUID.
    """
    assert len(args) == 2, "qviewkit-url only takes a single argument!"
    uuid, kvargs = QviewkitURLParser.parse(args[1])

    qkit.start()
    file = qkit.fid.get(uuid)
    repo = qkit.cfg.get("repo_path", default=None)
    if file is None and repo is not None:
        # Try looking for breadcrumbs
        file = breadcrumb_search(Path(repo), uuid)

    if file is not None:  # Success!
        main(argv=[args[0], "-f", str(file)])
    else:  # Failure...
        main(argv=[args[0]])  # Opening an empty window to signal an error.

def breadcrumb_search(directory: Path, target_uuid: str, max_bruteforce_depth: int = 3) -> Optional[str]:
    """
    Search based on breadcrumbs. Each backed-up computer creates a local index of known UUIDs. Applies to old
    files only in a limited fashion.
    """
    local_known_uuids = breadcrumbs.read_breadcrumbs(directory)
    if len(local_known_uuids.keys()) != 0:  # This is an indexed data_dir
        if target_uuid in local_known_uuids:
            path = local_known_uuids[target_uuid]
            return str(path)  # We found the file, return it.
        else:
            return None  # We do not expect any results below this point.
    elif max_bruteforce_depth > 0:  # Unindexed directory
        for child in directory.iterdir():
            if child.is_dir():  # Go into the child directories
                result = breadcrumb_search(child, target_uuid, max_bruteforce_depth=max_bruteforce_depth - 1)
                if result is not None:
                    return result
    return None