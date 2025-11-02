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

"""WorkflowRunStep implementation."""

from pathlib import Path

from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.variable import push_variables

__all__ = ["WorkflowRunStep"]


class WorkflowRunStep(Step):
    """Run another workflow."""

    path: Path
    fail_fast: bool
    chdir: Path | None

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(
            format_auto(
                self.raw_data["workflow"],
                mode=FormatMode.EXECUTE,
                valtype=str,
            ),
        )
        self.fail_fast = format_auto(
            self.raw_data.get("fail-fast", True),
            mode=FormatMode.EXECUTE,
            valtype=bool,
        )
        chdir = format_auto(
            self.raw_data.get("chdir", None),
            mode=FormatMode.EXECUTE,
            valtype=str | None,
        )
        self.chdir = Path(chdir) if chdir else None

    def run(self) -> None:
        """Run the step."""
        exc = WorkflowInterfaces.get_run_workflow()(
            self.path,
            fail_fast=self.fail_fast,
            chdir=self.chdir,
        )
        if exc:
            push_variables(f"{self.global_id}.exception", exc)
