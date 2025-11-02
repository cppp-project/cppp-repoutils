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

"""MkdirStep implementation."""

from pathlib import Path
from typing import cast

from rubisco.kernel.workflow.step import Step
from rubisco.lib.fileutil import assert_rel_path
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["MkdirStep"]


class MkdirStep(Step):
    """Make directories."""

    paths: list[Path]

    def init(self) -> None:
        """Initialize the step."""
        paths = cast(
            "str | list[str]",
            format_auto(
                self.raw_data["mkdir"],
                mode=FormatMode.EXECUTE,
                valtype=str | list[str],
            ),
        )
        self.paths = (
            [Path(paths)]
            if isinstance(paths, str)
            else [Path(p) for p in paths]
        )

    def run(self) -> None:
        """Run the step."""
        for path in self.paths:
            call_ktrigger(IKernelTrigger.on_mkdir, path=path)
            assert_rel_path(path)
            path.mkdir(exist_ok=True, parents=True)
