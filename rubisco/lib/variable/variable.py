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

"""Rubisco variable system."""

from typing import Any

from rubisco.lib.stack import Stack
from rubisco.lib.variable.callbacks import undefined_var_callbacks

__all__ = [
    "get_variable",
    "has_variable",
    "pop_variables",
    "push_variables",
    "variables",
]

# The global variable container.
variables: dict[str, Stack[Any]] = {}


def push_variables(
    name: str,
    value: Any,  # noqa: ANN401
) -> None:
    """Push a new variable.

    Args:
        name (str): The name of the variable.
        value (Any): The value of the variable.

    """
    if name in variables:
        variables[name].put(value)
    else:
        variables[name] = Stack()
        variables[name].put(value)


def pop_variables(
    name: str,
    *,
    default: Any = None,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Pop the top value of the given variable.

    If the name undefined, return None.

    Args:
        name (str): The name of the variable.
        default (Any): The default value of the variable.
            Defaults to None.

    Returns:
        Any: The top value of the given variable.

    """
    if name in variables:
        res = variables[name].get()
        if variables[name].empty():
            del variables[name]
        return res
    return default


def has_variable(
    name: str,
) -> bool:
    """Check if the variable exists.

    Args:
        name (str): The name of the variable.

    Returns:
        bool: True if the variable exists, False otherwise.

    """
    return name in variables


def get_variable(
    name: str,
    *,
    default: Any = ...,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.
        default (Any): The default value of the variable.
            Defaults to Ellipsis. If it is Ellipsis and the variable is not
            found, raise KeyError.
        src_ref (dict[str, Stack]): The source dictionary.
            Defaults to `variables`, the global variable container.

    Returns:
        Any: The value of the given variable.

    Raises:
        KeyError: If the variable is not found.

    """
    if name in variables:
        return variables[name].top()

    # If the variable is not found, call the callbacks.
    for callback in undefined_var_callbacks:
        callback(name)

    if name in variables:
        return variables[name].top()

    if default is ...:
        raise KeyError(name)
    return default
