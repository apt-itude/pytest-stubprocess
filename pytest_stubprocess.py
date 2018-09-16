# -*- coding: utf-8 -*-

import contextlib
import os
import sys

import attr
import pytest


@pytest.fixture
def stubprocess(mocker):
    return Registry(
        mocker.patch('_posixsubprocess.fork_exec'),
        mocker.patch('os.waitpid'),
        mocker.patch('os.kill'),
    )


@attr.s
class Registry:

    _mock_fork_exec = attr.ib()
    _mock_waitpid = attr.ib()
    _mock_kill = attr.ib()
    _executables = attr.ib(default=attr.Factory(dict))
    _return_codes = attr.ib(default=attr.Factory(dict))
    _latest_pid = 0

    def __attrs_post_init__(self):
        self._mock_fork_exec.side_effect = self._fork_exec
        self._mock_waitpid.side_effect = self._waitpid
        self._mock_kill.side_effect = self._kill

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

        pid = self._get_next_pid()

        run_context = contextlib.ExitStack()

        if c2pwrite >= 0:
            run_context.enter_context(self._redirect_stdout_to_fd(c2pwrite))

        if errwrite >= 0:
            run_context.enter_context(self._redirect_stderr_to_fd(errwrite))

        run_context.enter_context(self._handle_exit(pid))

        with run_context:
            executable(args)

        return pid

    def _get_next_pid(self):
        next_pid = self._latest_pid + 1
        self._latest_pid = next_pid
        return next_pid

    def _redirect_stdout_to_fd(self, fd):
        stdout = os.fdopen(fd, mode='w', closefd=False)
        return contextlib.redirect_stdout(stdout)

    def _redirect_stderr_to_fd(self, fd):
        stderr = os.fdopen(fd, mode='w', closefd=False)
        return contextlib.redirect_stderr(stderr)

    @contextlib.contextmanager
    def _handle_exit(self, pid):
        try:
            yield
        except SystemExit as err:
            if isinstance(err.code, str):
                print(err.code, file=sys.stderr)
                return_code = 1
            else:
                return_code = err.code
        else:
            return_code = 0

        self._return_codes[pid] = return_code

    def _waitpid(self, pid, _options):
        try:
            return_code = self._return_codes.pop(pid)
        except KeyError:
            raise ChildProcessError

        return pid, return_code

    def _kill(self, pid, signal):
        pass
