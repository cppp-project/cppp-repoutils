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

"""ExtensionLoadStep implementation."""

from pathlib import Path
from typing import cast

from rubisco.envutils.env import GLOBAL_ENV, USER_ENV, WORKSPACE_ENV
from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import FormatMode, format_auto

__all__ = ["ExtensionLoadStep"]


class ExtensionLoadStep(Step):
    """Load a Rubisco Excention manually."""

    path: Path

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(
            cast(
                "str",
                format_auto(
                    self.raw_data["extension"],
                    mode=FormatMode.EXECUTE,
                    valtype=str,
                ),
            ),
        )

    def run(self) -> None:
        """Run the step."""
        load_extension = WorkflowInterfaces.get_load_extension()
        load_extension(self.path, WORKSPACE_ENV, strict=True)
        load_extension(self.path, USER_ENV, strict=True)
        load_extension(self.path, GLOBAL_ENV, strict=True)
