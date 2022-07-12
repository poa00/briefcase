import os
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.windows.app import WindowsAppRunCommand


def test_run_app(first_app_config, tmp_path):
    """A windows app can be started."""
    command = WindowsAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()

    command.run_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "windows" / "app" / "First App" / "src" / "First App.exe"
            ),
        ],
        check=True,
        env={
            "FIRST_APP_LOG_DIR": tmp_path,
        },
    )


def test_run_app_failed(first_app_config, tmp_path):
    """If there's a problem started the app, an exception is raised."""
    command = WindowsAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = BriefcaseCommandError("problem")

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "windows" / "app" / "First App" / "src" / "First App.exe"
            ),
        ],
        check=True,
        env={
            "FIRST_APP_LOG_DIR": tmp_path,
        },
    )
