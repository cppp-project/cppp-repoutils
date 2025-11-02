# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2025 The C++ Plus Project.
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

"""SetvarStep, PopvarStep implementation."""

from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import FormatMode, format_auto, format_str
from rubisco.lib.variable.variable import pop_variables, push_variables

__all__ = ["PopvarStep", "SetvarStep"]


class SetvarStep(Step):
    """Set a variable."""

    var_name: str
    var_value: object
    format_recursive: bool  # If true, format the value if it is a list or dict.

    def init(self) -> None:
        """Initialize the step."""
        self.var_name = format_auto(
            self.raw_data["var"],
            mode=FormatMode.EXECUTE,
            valtype=str,
        )
        self.format_recursive = format_auto(
            self.raw_data.get("format-recursive", True),
            mode=FormatMode.EXECUTE,
            valtype=bool,
        )
        # Format it later, when it is used.
        # But I don't know why I have to do this.
        self.var_value = self.raw_data["value"]

    def run(self) -> None:
        """Run the step."""
        push_variables(
            self.var_name,
            format_auto(
                self.var_value,
                mode=FormatMode.EXECUTE,
                valtype=object,
            )
            if not self.format_recursive
            else format_str(
                self.var_value,
                mode=FormatMode.EXECUTE,
                valtype=object,
            ),
        )


class PopvarStep(Step):
    """Pop a variable."""

    var_name: str

    def init(self) -> None:
        """Initialize the step."""
        self.var_name = format_auto(
            self.raw_data["popvar"],
            mode=FormatMode.EXECUTE,
            valtype=str,
        )

    def run(self) -> None:
        """Run the step."""
        pop_variables(self.var_name)
