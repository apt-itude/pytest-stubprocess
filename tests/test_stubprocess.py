# -*- coding: utf-8 -*-

import subprocess
import sys

import pytest


class TestStdout:

    @pytest.fixture(autouse=True)
    def exe(self, stubprocess):
        stubprocess.register(
            'test',
            lambda argv: print(f'args: {argv}')
        )

    def test_default(self, capfd):
        subprocess.run(['test', 'writing', 'to', 'stdout'])

        stdout, _ = capfd.readouterr()

        assert stdout == "args: ['test', 'writing', 'to', 'stdout']\n"

    def test_pipe(self):
        result = subprocess.run(
            ['test', 'writing', 'to', 'stdout'],
            stdout=subprocess.PIPE,
        )

        assert result.stdout == b"args: ['test', 'writing', 'to', 'stdout']\n"

    def test_devnull(self, capfd):
        result = subprocess.run(
            ['test', 'writing', 'to', 'stdout'],
            stdout=subprocess.DEVNULL,
        )

        stdout, _ = capfd.readouterr()

        assert stdout == ""


class TestStderr:

    @pytest.fixture(autouse=True)
    def exe(self, stubprocess):
        stubprocess.register(
            'test',
            lambda argv: print(f'args: {argv}', file=sys.stderr)
        )

    def test_default(self, capfd):
        subprocess.run(['test', 'writing', 'to', 'stderr'])

        _, stderr = capfd.readouterr()

        assert stderr == "args: ['test', 'writing', 'to', 'stderr']\n"

    def test_pipe(self):
        result = subprocess.run(
            ['test', 'writing', 'to', 'stderr'],
            stderr=subprocess.PIPE,
        )

        assert result.stderr == b"args: ['test', 'writing', 'to', 'stderr']\n"

    def test_devnull(self, capfd):
        result = subprocess.run(
            ['test', 'writing', 'to', 'stderr'],
            stderr=subprocess.DEVNULL,
        )

        _, stderr = capfd.readouterr()

        assert stderr == ""


class TestExitHandling:

    @pytest.fixture(autouse=True)
    def exe(self, stubprocess):
        stubprocess.register('test', self.execute)

    def execute(self, argv):
        if len(argv) < 2:
            sys.exit('arguments are required')

        if len(argv) > 4:
            sys.exit(4)

        int(argv[2])

    def test_success(self):
        result = subprocess.run(
            ['test', 'with', '4', 'args'],
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0
        assert result.stderr == b''

    def test_failure_with_message(self):
        result = subprocess.run(
            ['test'],
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 1
        assert result.stderr == b'arguments are required\n'

    def test_failure_with_code(self):
        result = subprocess.run(
            ['test', 'with', 'too', 'many', 'args'],
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 4
        assert result.stderr == b''

    def test_failure_with_exception(self):
        result = subprocess.run(
            ['test', 'with', 'four', 'args'],
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 1
        assert (
            b"ValueError: invalid literal for int() with base 10: 'four'\n"
        ) in result.stderr
