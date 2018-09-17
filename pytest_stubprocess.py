# -*- coding: utf-8 -*-

import multiprocessing
import os
import sys

import attr
import pytest


@pytest.fixture
def stubprocess(mocker):
    return Registry(mocker.patch('_posixsubprocess.fork_exec'))


@attr.s
class Registry:

    _mock_fork_exec = attr.ib()
    _executables = attr.ib(default=attr.Factory(dict))
    _processes = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        self._mock_fork_exec.side_effect = self._fork_exec

    def register(self, name, executable):
        self._executables[name] = executable

    def _fork_exec(
        self,
        args,
        executable_list,
        close_fds,
        fds_to_keep,
        cwd,
        env,
        p2cread,
        p2cwrite,
        c2pread,
        c2pwrite,
        errread,
        errwrite,
        errpipe_read,
        errpipe_write,
        restore_signals,
        call_setsid,
        preexec_fn,
    ):
        name = args[0]
        try:
            executable = self._executables[name]
        except KeyError:
            # TODO(): pass correct args
            raise FileNotFoundError

        def run():
            if c2pwrite >= 0:
                sys.stdout = os.fdopen(c2pwrite, mode='w', closefd=False)

            if errwrite >= 0:
                sys.stderr = os.fdopen(errwrite, mode='w', closefd=False)

            executable(args)

        process = multiprocessing.Process(target=run)
        process.start()

        self._processes[process.pid] = process

        return process.pid
