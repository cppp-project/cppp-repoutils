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

"""CompressStep implementation."""

from pathlib import Path
from typing import cast

from rubisco.kernel.workflow.step import Step
from rubisco.lib.archive import compress
from rubisco.lib.variable.format import FormatMode, format_auto

__all__ = ["CompressStep"]


class CompressStep(Step):
    """Make a compressed archive."""

    src: Path
    dst: Path
    start: Path | None
    excludes: list[str] | None
    compress_format: str | list[str] | None
    compress_level: int | None
    overwrite: bool

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(
            cast(
                "str",
                format_auto(
                    self.raw_data["compress"],
                    mode=FormatMode.EXECUTE,
                    valtype=str,
                ),
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
        _start = cast(
            "str | None",
            format_auto(
                self.raw_data.get("start", None),
                mode=FormatMode.EXECUTE,
                valtype=str | None,
            ),
        )
        self.start = Path(_start) if _start else None
        self.excludes = cast(
            "list[str] | None",
            format_auto(
                self.raw_data.get("excludes", None),
                mode=FormatMode.EXECUTE,
                valtype=list | None,
            ),
        )
        self.compress_format = cast(
            "str | list[str] | None",
            format_auto(
                self.raw_data.get("format", None),
                mode=FormatMode.EXECUTE,
                valtype=str | list | None,
            ),
        )
        self.compress_level = cast(
            "int | None",
            format_auto(
                self.raw_data.get("level", None),
                mode=FormatMode.EXECUTE,
                valtype=int | None,
            ),
        )
        self.overwrite = cast(
            "bool",
            format_auto(
                self.raw_data.get("overwrite", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )

    def run(self) -> None:
        """Run the step."""
        if isinstance(self.compress_format, list):
            for fmt in self.compress_format:
                if fmt == "gzip":
                    ext = ".gz"
                elif fmt == "bzip2":
                    ext = ".bz2"
                elif fmt == "lzma":
                    ext = ".xz"
                elif fmt == "tgz":
                    ext = ".tar.gz"
                elif fmt == "tbz2":
                    ext = ".tar.bz2"
                elif fmt == "txz":
                    ext = ".tar.xz"
                else:
                    ext = f".{fmt}"

                dst = Path(str(self.dst) + ext)
                compress(
                    self.src,
                    dst,
                    self.start,
                    self.excludes,
                    fmt,
                    self.compress_level,
                    overwrite=self.overwrite,
                )
        else:
            compress(
                self.src,
                self.dst,
                self.start,
                self.excludes,
                self.compress_format,
                self.compress_level,
                overwrite=self.overwrite,
            )
