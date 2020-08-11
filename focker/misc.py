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


class FockerLock:
    """
    This class provides a simple context manager to make sure that only one focker Process accesses or modifies
    volatile data.

    Usage::

      from focker.misc import FockerLock
      with FockerLock():
          print("This runs with lock.")

    It is also possible to reverse the locking mechanism, releasing the lock within the context.

    Reversed usage::

      from focker.misc import FockerLock
      with FockerLock() as outerlock:
        print("This runs with lock.")
        with FockerLock(reverse=True) as innerlock:
            print("This runs without lock.")
        print("This runs with lock again.")

    :param reverse: If ``True``, the lock is released within the context, defaults to ``False``
    """
    fd = None

    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def aquire(self):
        """
        Aquires the lock. Albeit this method is exposed, it's direct use should be avoided unless strictly necessary.

        .. info::
           Usage of the :class:`focker.misc.FockerLock` as context manager is strongly preferred, as this guarantees always
           releasing the lock.

        Usage::

          from focker.misc import FockerLock
          flock = FockerLock()
          flock.aquire()
          try:
              print("This runs with lock.")
          finally:
              flock.release()
        """
        os.makedirs(config.LOCKDIR, exist_ok=True)
        if self.fd is None:
            self.fd = open(config.LOCKFILE, 'a+')
        print(f'Waiting for {config.LOCKFILE} ...')
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        print('Lock acquired.')

    def release(self):
        """
        Releases the lock. Albeit this method is exposed, it's direct use should be avoided unless strictly necessary.

        .. info::
           Usage of the :class:`focker.misc.FockerLock` as context manager is strongly preferred, as this guarantees always
           releasing the lock.

        Usage::

          from focker.misc import FockerLock
          flock = FockerLock()
          flock.aquire()
          try:
              print("This runs with lock.")
          finally:
              flock.release()
        """
        if self.fd is None:
            return
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        print('Lock released')

    def __enter__(self):
        """
        This method is called upon entering the context.
        Decides if the lock is to be released or aquired.
        """
        if self.reverse:
            self.release()
        else:
            self.aquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        This method is called upon leaving the context.
        Decides if the lock is to be aquired or released.

        :param exc_type: Unused. Type of Exception raised within the context.
        :param exc_val: Unused. Value of Exception raised within the context.
        :param exc_tb: Unused. Traceback of Exception raised within the context.
        """
        if self.reverse:
            self.aquire()
        else:
            self.release()
