from subprocess import PIPE
from unittest.mock import Mock, call, patch

import pytest

from wakepy.methods import macos


@pytest.mark.parametrize(
    "method_cls, expected_command",
    [
        (macos.CaffeinateKeepRunning, ["caffeinate"]),
        (macos.CaffeinateKeepPresenting, ["caffeinate", "-d"]),
    ],
)
def test_enter_mode_success(method_cls, expected_command):
    method = method_cls()

    with patch("wakepy.methods.macos.Popen") as popenmock:
        popenmock.return_value = Mock()
        retval = method.enter_mode()

    assert retval is None
    assert expected_command == method.command.split()
    popenmock.assert_called_with(expected_command, stdin=PIPE, stdout=PIPE)
    # Entering the mode sets the ._process
    assert method._process is popenmock.return_value


@pytest.mark.parametrize(
    "method_cls",
    [macos.CaffeinateKeepRunning, macos.CaffeinateKeepPresenting],
)
def test_exit_mode_success(method_cls):
    method = method_cls()

    method._process = Mock()
    retval = method.exit_mode()

    assert retval is None
    assert method._process.mock_calls == [call.terminate(), call.wait()]

    # Case: Mode not entered
    method = method_cls()
    retval = method.exit_mode()
    assert retval is None
