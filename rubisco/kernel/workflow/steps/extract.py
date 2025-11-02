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

"""ExtractStep implementation."""

from pathlib import Path
from typing import cast

from rubisco.kernel.workflow.step import Step
from rubisco.lib.archive import extract
from rubisco.lib.variable.format import FormatMode, format_auto

__all__ = ["ExtractStep"]


class ExtractStep(Step):
    """Extract a compressed archive."""

    src: Path
    dst: Path
    compress_format: str | None
    overwrite: bool
    password: str | None

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(
            cast(
                "str",
                format_auto(
                    self.raw_data["extract"],
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
        self.compress_format = cast(
            "str | None",
            format_auto(
                self.raw_data.get("type", None),
                mode=FormatMode.EXECUTE,
                valtype=str | None,
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
        self.password = cast(
            "str | None",
            format_auto(
                self.raw_data.get("password", None),
                mode=FormatMode.EXECUTE,
                valtype=str | None,
            ),
        )

    def run(self) -> None:
        """Run the step."""
        extract(
            self.src,
            self.dst,
            self.compress_format,
            self.password,
            overwrite=self.overwrite,
        )
