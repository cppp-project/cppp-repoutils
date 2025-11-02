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

"""CopyFileStep implementation."""

import glob
from pathlib import Path
from typing import cast

from rubisco.kernel.workflow.step import Step
from rubisco.lib.fileutil import (
    assert_rel_path,
    check_file_exists,
    copy_recursive,
    rm_recursive,
)
from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["CopyFileStep"]


class CopyFileStep(Step):
    """Copy files or directories."""

    srcs: list[str]
    dst: Path
    overwrite: bool
    keep_symlinks: bool
    excludes: list[str] | None

    def init(self) -> None:
        """Initialize the step."""
        srcs = cast(
            "str | list[str]",
            format_auto(
                self.raw_data["copy"],
                mode=FormatMode.EXECUTE,
                valtype=str | list,
            ),
        )
        self.dst = Path(
            cast(
                "str",
                format_auto(
                    self.raw_data["to"],
                    mode=FormatMode.EXECUTE,
                    valtype=str,
                ),
            ),
        )

        self.srcs = [srcs] if isinstance(srcs, str) else srcs

        self.overwrite = cast(
            "bool",
            format_auto(
                self.raw_data.get("overwrite", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.keep_symlinks = cast(
            "bool",
            format_auto(
                self.raw_data.get("keep-symlinks", False),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.excludes = cast(
            "list[str] | None",
            format_auto(
                self.raw_data.get("excludes", None),
                mode=FormatMode.EXECUTE,
                valtype=list[str] | None,
            ),
        )

    def run(self) -> None:
        """Run the step."""
        if self.overwrite and self.dst.exists() and not self.dst.is_dir():
            rm_recursive(self.dst, strict=True)
        if self.dst.exists() and not self.dst.is_dir():
            check_file_exists(self.dst)
        assert_rel_path(self.dst)

        matched: bool = False
        for src_glob in self.srcs:
            files = glob.glob(src_glob)  # noqa: PTH207
            if files:
                matched = True
            for src in files:
                src_path = Path(src)
                call_ktrigger(
                    IKernelTrigger.on_copy,
                    src=src_path,
                    dst=self.dst,
                )
                copy_recursive(
                    src_path,
                    self.dst,
                    self.excludes,
                    strict=not self.overwrite,
                    symlinks=self.keep_symlinks,
                    exists_ok=self.overwrite,
                )
        if not matched:
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _("No file matched the glob pattern: ${{glob}}."),
                    fmt={"glob": repr(self.srcs)},
                ),
            )
