# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
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

"""A variable container.

This module provides a context manager for variable substitution in strings.
It allows for the temporary replacement of variables in a string with
their corresponding values from a dictionary. Restoring the
original values when the context is exited.
"""

from types import TracebackType
from typing import Any, Self

from rubisco.lib.variable.variable import pop_variables, push_variables

__all__ = ["VariableContainer"]


class VariableContainer:
    """The variable container."""

    def __init__(self, fmt: dict[str, Any] | None = None) -> None:
        """Initialize the variable container.

        Args:
            fmt (dict[str, Any] | None): The format dictionary.
                Defaults to None.

        """
        self._fmt = fmt or {}

    def __enter__(self) -> Self:
        """Enter the variable container.

        Returns:
            Self: The variable container.

        """
        for key, value in self._fmt.items():
            push_variables(key, value)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the variable container.

        Args:
            exc_type (Any): The exception type.
            exc_value (Any): The exception value.
            traceback (Any): The traceback.

        """
        for key in self._fmt:
            pop_variables(key)
