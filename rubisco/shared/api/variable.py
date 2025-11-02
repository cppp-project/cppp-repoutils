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

"""Rubisco variable system."""

from typing import Any

from rubisco.lib.stack import Stack
from rubisco.lib.typecheck import (
    ValType,
    get_dict_check,
    get_list_check,
    is_instance,
    rubisco_isinstance,
    type_assert,
)
from rubisco.lib.variable.builtin_vars import init_builtin_vars
from rubisco.lib.variable.callbacks import add_undefined_var_callback
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.format import (
    FormatMode,
    format_auto,
    format_dict,
    format_list,
    format_str,
)
from rubisco.lib.variable.pyexpr_sandbox import eval_pyexpr
from rubisco.lib.variable.utils import make_pretty, merge_dict
from rubisco.lib.variable.var_container import VariableContainer
from rubisco.lib.variable.variable import (
    get_variable,
    pop_variables,
    push_variables,
)
from rubisco.lib.variable.variable import (
    variables as _variables,
)

__all__ = [
    "FormatMode",
    "ValType",
    "VariableContainer",
    "add_undefined_var_callback",
    "eval_pyexpr",
    "fast_format_str",
    "format_auto",
    "format_dict",
    "format_list",
    "format_str",
    "get_dict_check",
    "get_list_check",
    "get_orig_variables",
    "get_variable",
    "get_variables",
    "get_variables",
    "init_builtin_vars",
    "is_instance",
    "make_pretty",
    "merge_dict",
    "pop_variables",
    "push_variables",
    "rubisco_isinstance",
    "type_assert",
]


def get_orig_variables() -> dict[str, Stack[Any]]:
    """Get original variables list with stack info.

    Warning:
        This function will return the original variables list, if you update
        the returned dictionary, it will update the original variables list.

    Returns:
        dict[str, Stack[Any]]: The original variables list with stack info.

    """
    return _variables


def get_variables() -> dict[str, Any]:
    """Get variables list.

    Returns:
        dict[str, Any]: The variables list.

    """
    return {k: v.top() for k, v in _variables.items()}
