import os
import shutil
import sys
from unittest import mock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    MissingNetworkResourceError,
    MissingStubBinary,
    NetworkFailure,
)

from ...utils import create_file, create_zip_file, mock_zip_download


@pytest.mark.parametrize("console_app", [True, False])
def test_install_stub_binary(
    create_command,
    myapp,
    console_app,
    stub_binary_revision_path_index,
    tmp_path,
):
    """A stub binary can be downloaded and unpacked where it is needed."""
    # Mock the app type
    myapp.console_app = console_app
    stub_name = "Console-Stub" if console_app else "GUI-Stub"

    # Mock download.file to return a support package
    create_command.tools.download.file = mock.MagicMock(
        side_effect=mock_zip_download(
            f"{stub_name}-3.X-b37.zip",
            [(f"{stub_name}.bin", "stub binary")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.download.file.assert_called_with(
        download_path=create_command.data_path / "stub",
        url=f"https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/{stub_name}-3.X-b37.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        tmp_path / f"data/stub/{stub_name}-3.X-b37.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / f"base_path/build/my-app/tester/dummy/{stub_name}.bin").exists()


@pytest.mark.parametrize("console_app", [True, False])
def test_install_pinned_stub_binary(
    create_command,
    myapp,
    console_app,
    stub_binary_revision_path_index,
    tmp_path,
):
    """The stub binary revision can be pinned."""
    # Pin the stub binary revision
    myapp.stub_binary_revision = 42

    # Mock the app type
    myapp.console_app = console_app
    stub_name = "Console-Stub" if console_app else "GUI-Stub"

    # Mock download.file to return a support package
    create_command.tools.download.file = mock.MagicMock(
        side_effect=mock_zip_download(
            f"{stub_name}-3.X-b42.zip",
            [(f"{stub_name}.bin", "stub binary")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.download.file.assert_called_with(
        download_path=create_command.data_path / "stub",
        url=f"https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/{stub_name}-3.X-b42.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        tmp_path / f"data/stub/{stub_name}-3.X-b42.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / f"base_path/build/my-app/tester/dummy/{stub_name}.bin").exists()


def test_install_stub_binary_missing(
    create_command,
    myapp,
    stub_binary_revision_path_index,
    tmp_path,
):
    """If the system-nominated stub binary doesn't exist, a specific error is raised."""
    # Modify download.file to raise an exception
    create_command.tools.download.file = mock.MagicMock(
        side_effect=MissingNetworkResourceError(
            "https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/GUI-Stub-3.X-b37.zip"
        )
    )

    # Install the support package; this will raise a custom exception
    with pytest.raises(
        MissingStubBinary,
        match=r"Unable to download Tester stub binary for Python 3.X on gothic",
    ):
        create_command.install_stub_binary(myapp)


def test_install_custom_stub_binary_url(
    create_command,
    myapp,
    stub_binary_revision_path_index,
    tmp_path,
):
    """A stub binary can be downloaded and unpacked where it is needed."""
    # Provide an app-specific override of the stub binary as a URL
    myapp.stub_binary = "https://example.com/custom/My-Stub.zip"

    # Mock download.file to return a support package
    create_command.tools.download.file = mock.MagicMock(
        side_effect=mock_zip_download(
            "My-Stub.zip",
            [("GUI-Stub.bin", "stub binary")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.download.file.assert_called_with(
        download_path=create_command.data_path
        / "stub/986428ef9d5a1852fc15d4367f19aa328ad530686056e9d83cdde03407c0bceb",
        url="https://example.com/custom/My-Stub.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        tmp_path
        / "data/stub/986428ef9d5a1852fc15d4367f19aa328ad530686056e9d83cdde03407c0bceb/My-Stub.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/GUI-Stub.bin").exists()


def test_install_custom_stub_binary_file(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
):
    """A custom support package can be specified as a local file."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/My-Stub")

    # Write a temporary support binary
    create_file(tmp_path / "custom/My-Stub", "Custom stub")

    # Modify download.file to return the temp zipfile
    create_command.tools.download.file = mock.MagicMock()

    # Mock shutil so we can confirm that unpack isn't called,
    # but we still want the side effect of calling
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.copyfile.side_effect = shutil.copyfile

    # Install the support package
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.download.file.assert_not_called()

    # The file isn't an archive, so it hasn't been unpacked.
    create_command.tools.shutil.unpack_archive.assert_not_called()

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/GUI-Stub.bin").exists()


def test_install_custom_stub_binary_archive(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
):
    """A custom support package can be specified as a local archive."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/support.zip")

    # Write a temporary support zip file
    support_file = create_zip_file(
        tmp_path / "custom/support.zip",
        [("GUI-Stub.bin", "Custom stub")],
    )

    # Modify download.file to return the temp zipfile
    create_command.tools.download.file = mock.MagicMock()

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.download.file.assert_not_called()

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        support_file,
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/GUI-Stub.bin").exists()


def test_install_custom_stub_binary_with_revision(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
    capsys,
):
    """If a custom stub binary file also specifies a revision, the revision is ignored
    with a warning."""
    # Provide an app-specific override of the stub binary, *and* the revision
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/support.zip")
    myapp.stub_binary_revision = "42"

    # Write a temporary support zip file
    support_file = create_zip_file(
        tmp_path / "custom/support.zip",
        [("GUI-Stub.bin", "Custom stub")],
    )

    # Modify download.file to return the temp zipfile
    create_command.tools.download.file = mock.MagicMock()

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.download.file.assert_not_called()

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        support_file,
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the support file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/GUI-Stub.bin").exists()

    # A warning about the support revision was generated.
    assert "stub binary revision will be ignored." in capsys.readouterr().out


def test_install_custom_stub_binary_with_invalid_url(
    create_command,
    myapp,
    stub_binary_revision_path_index,
):
    """Invalid URL for a custom support package raises MissingNetworkResourceError."""

    # Provide an custom stub binary URL
    url = "https://example.com/custom/support.zip"
    myapp.stub_binary = url

    # Modify download.file to raise an exception
    create_command.tools.download.file = mock.MagicMock(
        side_effect=MissingNetworkResourceError(url)
    )

    # The bad URL should raise a MissingNetworkResourceError
    with pytest.raises(MissingNetworkResourceError):
        create_command.install_stub_binary(myapp)

    # However, there will have been a download attempt
    create_command.tools.download.file.assert_called_with(
        download_path=(
            create_command.data_path
            / "stub"
            / "55441abbffa311f65622df45a943afc347a21ab40e8dcec79472c92ef467db24"
        ),
        url=url,
        role="stub binary",
    )


def test_offline_install(
    create_command,
    myapp,
    stub_binary_revision_path_index,
):
    """If the computer is offline, an error is raised."""
    create_command.tools.requests.get = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        create_command.install_stub_binary(myapp)
