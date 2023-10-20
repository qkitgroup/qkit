import os
from argparse import ArgumentParser, FileType
import pathlib
import logging

def index_directory():
    parser = ArgumentParser(description="Index a directory as a datadir and create a cache in place.")
    parser.add_argument("--datadir", default=os.getcwd(), type=pathlib.Path)
    args = parser.parse_args()

    import qkit
    # Setup directories.
    qkit.cfg['datadir'] = args.datadir
    qkit.cfg['logdir'] = os.path.join(args.datadir, "index-logs")
    qkit.cfg['use_datadir_cache'] = False
    qkit.cfg['file_log_level'] = 'INFO'
    qkit.cfg['stdout_log_level'] = 'INFO'

    # Check if it exists
    if not os.path.exists(qkit.cfg['logdir']):
        os.mkdir(qkit.cfg['logdir'])

    assert os.path.isdir(qkit.cfg['logdir']), f"The assumed log directory {qkit.cfg['logdir']} is not a directory!"

    # Configure a bare-bones qkit
    qkit.cfg.preset_analyse()

    # We need to start qkit, as it then loads the fid.
    qkit.start(silent=True)
    # This acquires the lock. If loading has finished, the lock is released and we continue.
    logging.info(f"Indexed measurements up to {qkit.fid.get_last()}")
