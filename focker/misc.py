#
# Copyright (C) Stanislaw Adaszewski, 2020
# License: GNU General Public License v3.0
# URL: https://github.com/sadaszewski/focker
# URL: https://adared.ch/focker
#

import random
from .zfs import zfs_exists
import os
import fcntl
import hashlib

import focker.config as config


def filehash(fname):
    h = hashlib.sha256()
    with open(fname, 'rb') as f:
        while True:
            data = f.read(1024*1024*4)
            if not data:
                break
            h.update(data)
    res = h.hexdigest()
    return res


def random_sha256_hexdigest():
    for _ in range(10**6):
        res = bytes([ random.randint(0, 255) for _ in range(32) ]).hex()
        if not res[:7].isnumeric():
            return res
    raise ValueError('Couldn\'t find random SHA256 hash with non-numeric 7-character prefix in 10^6 trials o_O')


def find_prefix(head, tail):
    for pre in range(7, len(tail)):
        name = head + tail[:pre]
        if not zfs_exists(name):
            break
    return name


def focker_lock():
    os.makedirs(config.LOCKDIR, exist_ok=True)
    if focker_lock.fd is None:
        focker_lock.fd = open(config.LOCKFILE, 'a+')
    print(f'Waiting for {config.LOCKFILE} ...')
    fcntl.flock(focker_lock.fd, fcntl.LOCK_EX)
    print('Lock acquired.')
focker_lock.fd = None


def focker_unlock():
    if focker_lock.fd is None:
        return
    fcntl.flock(focker_lock.fd, fcntl.LOCK_UN)
    print('Lock released')
