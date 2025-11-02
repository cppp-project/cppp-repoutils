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

"""ShellExecStep implementation."""

from pathlib import Path
from typing import Any

from rubisco.kernel.workflow.step import Step
from rubisco.lib.process import Process
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.variable import push_variables

__all__ = ["ShellExecStep"]


class ShellExecStep(Step):
    """A shell execution step."""

    cmd: str | list[Any]
    cwd: Path
    fail_on_error: bool

    def init(self) -> None:
        """Initialize the step."""
        self.cmd = format_auto(
            self.raw_data["run"],
            mode=FormatMode.EXECUTE,
            valtype=str | list,
        )
        self.cwd = Path(
            format_auto(
                self.raw_data.get("cwd", "."),
                mode=FormatMode.EXECUTE,
                valtype=str,
            ),
        )
        self.fail_on_error = format_auto(
            self.raw_data.get("fail-on-error", True),
            mode=FormatMode.EXECUTE,
            valtype=bool,
        )

    def run(self) -> None:
        """Run the step."""
        retcode = Process(self.cmd, self.cwd).run(
            fail_on_error=self.fail_on_error,
        )
        push_variables(f"{self.global_id}.retcode", retcode)
