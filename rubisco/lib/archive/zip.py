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

"""Zip compress/extract utilities."""

import os
import time
import zipfile
from pathlib import Path

from rubisco.config import DEFAULT_CHARSET
from rubisco.kernel.config_file import config_file
from rubisco.lib.archive.utils import get_includes, write_to_archive
from rubisco.lib.fileutil import check_file_exists, rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

# pylint: disable=R0801

__all__ = ["compress_zip", "extract_zip"]


def extract_zip(
    file: Path,
    dest: Path,
    password: str | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Extract zip file to destination.

    Args:
        file (Path): Path to zip file.
        dest (Path): Destination directory.
        password (str): Password to decrypt zip file. Default is None.
        overwrite (bool): Overwrite destination directory if it exists.

    """
    with zipfile.ZipFile(file, "r") as fp:
        memembers = fp.infolist()
        if not overwrite:
            # Check if destination directory exists.
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)
        test_msg = fast_format_str(
            _(
                "Extracting ${{file}} to ${{path}} as '${{type}}' ...",
            ),
            fmt={
                "file": make_pretty(file),
                "path": make_pretty(dest),
                "type": "zip",
            },
        )
        task_name = _("Extracting")
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_start_msg=test_msg,
            task_name=task_name,
            total=len(memembers),
        )

        verbose = bool(
            get_dict_check(
                config_file.config,
                "verbose",
                valtype=bool,
                default=False,
            ),
        )
        for member in memembers:
            fp.extract(
                member,
                dest,
                pwd=password.encode(DEFAULT_CHARSET) if password else None,
            )
            perm = member.external_attr >> 16
            if perm:
                (dest / member.filename).chmod(perm)
            utime = member.date_time
            utime = time.mktime((*utime, 0, 0, -1))
            os.utime(dest / member.filename, (utime, utime))
            update_msg = make_pretty(dest / member.filename) if verbose else ""
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                update_msg=update_msg,
            )

        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def compress_zip(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_level: int | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Compress a zip file to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination zip file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.

    """
    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)
    task_start_msg = fast_format_str(
        _(
            "Compressing ${{path}} to ${{file}} as '${{type}}' ...",
        ),
        fmt={
            "path": make_pretty(src),
            "file": make_pretty(dest),
            "type": "zip",
        },
    )

    if not start:
        start = src.parent

    with zipfile.ZipFile(
        dest,
        "w",
        zipfile.ZIP_DEFLATED,
        compresslevel=compress_level,
    ) as fp:
        includes = get_includes(src, excludes)

        write_to_archive(
            includes,
            start,
            fp.write,
            task_start_msg=task_start_msg,
        )
