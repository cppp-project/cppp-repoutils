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

"""RemoveStep implementation."""

import glob
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.fileutil import rm_recursive
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["RemoveStep"]


class RemoveStep(Step):
    """Remove a file or directory.

    This step is dangerous. Use it with caution!
    """

    globs: list[str]
    excludes: list[str]
    include_hidden: bool

    def init(self) -> None:
        """Initialize the step."""
        remove = format_auto(
            self.raw_data["remove"],
            mode=FormatMode.EXECUTE,
            valtype=str | list[str],
        )
        self.globs = [remove] if isinstance(remove, str) else remove

        self.include_hidden = format_auto(
            self.raw_data.get("include-hidden", False),
            mode=FormatMode.EXECUTE,
            valtype=bool,
        )
        self.excludes = format_auto(
            self.raw_data.get("excludes", []),
            mode=FormatMode.EXECUTE,
            valtype=list[str],
        )

    def run(self) -> None:
        """Run the step."""
        for glob_partten in self.globs:
            paths = glob.glob(  # pylint: disable=E1123  # noqa: PTH207
                glob_partten,
                recursive=True,
                include_hidden=self.include_hidden,
            )
            for str_path in paths:
                path = Path(str_path)
                call_ktrigger(IKernelTrigger.on_remove, path=path)
                rm_recursive(path, strict=True)
