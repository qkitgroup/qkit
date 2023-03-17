# -*- coding: utf-8 -*-
"""
@author: S1@KIT/2018
This file checks if we are in a git environment and provides information about the last commit
"""
import logging
from os.path import join
from time import time

import qkit
if qkit.cfg.get('check_for_updates',False):
    try:
        with open(join(qkit.cfg['qkitdir'], '../.git/logs/HEAD'), 'rb') as f:
            f.seek(-1024, 2)
            last_commit = f.readlines()[-1].decode().split("\t")[0]  # The line looks like this: 0old_commit 1new_commit 2username 3mail 4timestamp 5timezone
            qkit.git = {
                'timestamp': float(last_commit.split(" ")[-2]),
                'commit_id': last_commit.split(" ")[1]
            }
            if (time() - qkit.git['timestamp']) / 3600 / 24 > 21:  # If the last commit is older than 3 weeks
                logging.warning("Your qkit version is older than 3 weeks. Please consider the 'git pull' command. We are usually trying to get better.")
    except Exception:
        qkit.git = {
            'timestamp': None,
            'commit_id': "UNTRACKED-NO_GIT_FOUND"
        }
        logging.info("You are not operating qkit from a git repository. You do not need to do so, but this is the easiest way to get always the latest version.")
else:
    qkit.cfg['check_for_updates'] = False
    logging.info("Not checking for updates.")