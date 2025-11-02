# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024-2025 The C++ Plus Project.
# This file is part of the Rubisco.
#
# Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""7Z compress/extract utilities."""

import contextlib
from pathlib import Path

import py7zr
import py7zr.callbacks

from rubisco.kernel.config_file import config_file
from rubisco.lib.archive.utils import get_includes, write_to_archive
from rubisco.lib.fileutil import check_file_exists, rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    call_ktrigger,
)

__all__ = ["compress_7z", "extract_7z"]


def extract_7z(
    file: Path,
    dest: Path,
    password: str | None = None,
) -> None:
    """Extract 7z file to destination.

    Args:
        file (Path): Path to 7z file.
        dest (Path): Destination directory.
        password (str): Password to decrypt 7z file. Default is None.

    """
    with py7zr.SevenZipFile(file, mode="r", password=password) as fp:
        task_msg = fast_format_str(
            _(
                "Extracting "  # Pylint think this is a duplicate code.
                "${{file}} to ${{path}} as '${{type}}' ...",
            ),
            fmt={
                "file": make_pretty(file),
                "path": make_pretty(dest),
                "type": "7z",
            },
        )

        task_name = _("Extracting")

        verbose = bool(
            get_dict_check(
                config_file.config,
                "verbose",
                valtype=bool,
                default=False,
            ),
        )

        class _ExtractCallback(py7zr.callbacks.ExtractCallback):
            end: bool = False

            def report_start_preparation(self) -> None:
                """When the extraction process is started.

                Report a start of preparation event such as making list of
                    files and looking into its properties.
                """
                self.end = False
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_start_msg=task_msg,
                    task_name=task_name,
                    total=float(len(fp.getnames())),
                )

            def report_start(
                self,
                processing_file_path: str,
                processing_bytes: int,
            ) -> None:
                """When the extraction process is started.

                Report a start event of specified archive file and its input
                    bytes.

                Args:
                    processing_file_path (str): Processing file path.
                    processing_bytes (int): Processing bytes.

                """

            def report_update(self, decompressed_bytes: int) -> None:
                """When the extraction process is updated.

                Report an event when large file is being extracted more than 1
                    second or when extraction is finished. Receives a number of
                    decompressed bytes since the last update.

                Args:
                    decompressed_bytes (int): Decompressed bytes.

                """

            def report_end(  # pylint: disable=unused-argument
                self,
                processing_file_path: str,
                wrote_bytes: int,  # noqa: ARG002
            ) -> None:
                """When the extraction process is finished.

                Report an end event of specified archive file and its output
                    bytes.

                Args:
                    processing_file_path (str): Processing file path.
                    wrote_bytes (int): Wrote bytes.

                """
                pfp = processing_file_path
                call_ktrigger(
                    IKernelTrigger.on_progress,
                    task_name=task_name,
                    current=1,
                    delta=True,
                    update_msg=make_pretty(dest / pfp) if verbose else "",
                )

            def report_warning(self, message: str) -> None:
                """When the extraction process is warned.

                Report an warning event with its message.

                Args:
                    message (str): Warning message.

                """
                call_ktrigger(
                    IKernelTrigger.on_warning,
                    message=message,
                )

            def report_postprocess(self) -> None:
                """When the extraction process is finished.

                Report a start of post processing event such as set file
                    properties and permissions or creating symlinks.
                """
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
                self.end = True

        callback = _ExtractCallback()
        fp.extractall(dest, callback=callback)

        while not callback.end:
            with contextlib.suppress(RuntimeError):
                fp.reporterd.join(0.01)  # type: ignore[attr-defined]


def compress_7z(  # pylint: disable=too-many-arguments
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Compress a 7z file to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination 7z file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.

    """
    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)
    task_name = fast_format_str(
        _(
            "Compressing ${{path}} "  # Pylint think this is a duplicate code.
            "to ${{file}} as '${{type}}' ...",
        ),
        fmt={
            "path": make_pretty(src),
            "file": make_pretty(dest),
            "type": "7z",
        },
    )

    if not start:
        start = src.parent

    with py7zr.SevenZipFile(
        dest,
        mode="w",
    ) as fp:
        includes = get_includes(src, excludes)

        write_to_archive(
            includes,
            start,
            lambda path, arcname: fp.write(path, str(arcname)),
            task_name,
        )
