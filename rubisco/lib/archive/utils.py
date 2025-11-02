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

"""Utilities for archive."""

from collections.abc import Callable
from pathlib import Path

from rubisco.kernel.config_file import config_file
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["get_includes", "write_to_archive"]


def get_includes(
    src: Path,
    excludes: list[str] | None = None,
) -> list[Path]:
    """Get included files list with includes and excludes.

    Args:
        src (Path): Source file or directory.
        excludes (list[str] | None, optional): List of excluded files.
            Defaults to None.

    Returns:
        list[Path]: Included files list.

    """
    _includes = src.rglob("*") if src.is_dir() else [src]
    includes: list[Path] = []
    for path in _includes:
        if excludes and any(path.match(ex) for ex in excludes):
            continue
        includes.append(path)
    return includes


def write_to_archive(
    includes: list[Path],
    start: Path,
    on_write: Callable[[Path, Path], None],
    task_start_msg: str,
) -> None:
    """Write files to archive.

    Args:
        includes (list[Path]): Included files list.
        start (Path | None, optional): Start directory. Defaults to None.
        on_write (Callable[[Path, Path], None]): Callback function to write
            file to archive. It takes two arguments: source file path and
            its arcname.
        task_start_msg (str): Task for this compress/archive operation.

    """
    task_name = _("Compressing")
    call_ktrigger(
        IKernelTrigger.on_new_task,
        task_start_msg=task_start_msg,
        task_name=task_name,
        total=len(includes),
    )

    verbose = bool(
        get_dict_check(
            config_file.config,
            "verbose",
            valtype=bool,
            default=False,
        ),
    )
    for path in includes:
        try:
            arcname = path.relative_to(start)
        except ValueError as exc:
            raise RUValueError(
                fast_format_str(
                    _(
                        "${{path}} is not in the subpath of ${{start}}",
                    ),
                    fmt={
                        "path": make_pretty(path),
                        "start": make_pretty(start),
                    },
                ),
            ) from exc
        on_write(path, arcname)
        call_ktrigger(
            IKernelTrigger.on_progress,
            task_name=task_name,
            current=1,
            delta=True,
            update_msg=make_pretty(path) if verbose else "",
        )
    call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)
