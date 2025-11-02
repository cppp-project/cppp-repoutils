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

"""EchoStep implementation."""

from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["EchoStep", "OutputStep"]


class EchoStep(Step):
    """Output a message."""

    msg: str

    def init(self) -> None:
        """Initialize the step."""
        msg = self.raw_data.get("output", None)
        if msg is None:
            msg = self.raw_data["echo"]

        self.msg = str(format_auto(msg, mode=FormatMode.EXECUTE))

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(IKernelTrigger.on_output, message=self.msg)


OutputStep = EchoStep
