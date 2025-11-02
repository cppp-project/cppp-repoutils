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

"""PopenStep implementation."""

from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.process import Process
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.variable import push_variables

__all__ = ["PopenStep"]


class PopenStep(Step):
    """Read the output of a shell command."""

    cmd: str | list[object]
    cwd: Path
    fail_on_error: bool
    stdout: bool
    stderr: int

    def init(self) -> None:
        """Initialize the step."""
        self.cmd = format_auto(
            self.raw_data["popen"],
            mode=FormatMode.EXECUTE,
            valtype=str | list[object],
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
        self.stdout = format_auto(
            self.raw_data.get("stdout", True),
            mode=FormatMode.EXECUTE,
            valtype=bool,
        )
        stderr_mode = format_auto(
            self.raw_data.get("stderr", True),
            mode=FormatMode.EXECUTE,
            valtype=bool | str,
        )
        if stderr_mode is True:
            self.stderr = 1
        elif stderr_mode is False:
            self.stderr = 0
        else:
            self.stderr = 2

    def run(self) -> None:
        """Run the step."""
        stdout, stderr, retcode = Process(self.cmd, cwd=self.cwd).popen(
            stdout=self.stdout,
            stderr=self.stderr,
            fail_on_error=self.fail_on_error,
            show_step=True,
        )
        push_variables(f"{self.global_id}.stdout", stdout)
        push_variables(f"{self.global_id}.stderr", stderr)
        push_variables(f"{self.global_id}.retcode", retcode)
