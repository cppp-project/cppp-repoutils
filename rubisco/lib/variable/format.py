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

"""Rubisco string formatter with variable."""

import enum
from collections.abc import Iterable
from typing import Any, cast

from rubisco.lib.typecheck import ValType, type_assert
from rubisco.lib.variable.execute import execute_expression
from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.ru_ast import parse_expression
from rubisco.lib.variable.var_container import VariableContainer

__all__ = [
    "FormatMode",
    "format_auto",
    "format_dict",
    "format_list",
    "format_str",
]


class FormatMode(enum.IntEnum):
    """Format mode enumeration."""

    NONE = 0b0
    EXECUTE = 0b1


def format_str[T](
    string: T,
    *,
    fmt: dict[str, Any] | None = None,
    mode: int = FormatMode.NONE,
    valtype: ValType[T] = object,
) -> T | Any:  # noqa: ANN401
    """Format the string with variables.

    Args:
        string (T): The string to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.
        mode (int): The format mode. Defaults to FormatMode.NONE.
            Be careful when using EXECUTE mode, as it may lead to RCE security
            issues.
        valtype (ValType[T] | None): The expected type of the result..

    Returns:
        T | Any: The formatted string. If the input is not a string,
            return itself.

    """
    if not isinstance(string, str):
        return string

    with VariableContainer(fmt):
        res = execute_expression(
            parse_expression(get_token(string)),
            enable_exec=bool(mode & FormatMode.EXECUTE),
        )
        type_assert(res, valtype)
        return res


def format_list[T](
    items: Iterable[T],
    *,
    fmt: dict[str, Any] | None = None,
    mode: int = FormatMode.NONE,
    valtype: ValType[T] = object,
) -> Any:  # noqa: ANN401
    """Format a list of items.

    Args:
        items (Iterable[T]): The items to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.
        mode (int): The format mode. Defaults to FormatMode.NONE.
        valtype (ValType[T] | None): The expected type of the
            result. Defaults to object.

    Returns:
        Any: The formatted items.

    """
    res: list[str | T] = []
    for item in items:
        if isinstance(item, list):
            res.append(
                cast(
                    "str | T",
                    format_list(
                        cast("Iterable[Any]", item),
                        fmt=fmt,
                        mode=mode,
                    ),
                ),
            )
        elif isinstance(item, dict):
            res.append(
                cast(
                    "str | T",
                    format_dict(
                        cast("dict[str, Any]", item),
                        fmt=fmt,
                        mode=mode,
                    ),
                ),
            )
        else:
            res.append(cast("str | T", format_str(item, fmt=fmt, mode=mode)))

    type_assert(res, valtype)

    return res


def format_dict[T](
    mapping: dict[str, T],
    *,
    fmt: dict[str, Any] | None = None,
    mode: int = FormatMode.NONE,
    valtype: ValType[T] = object,
) -> Any:  # noqa: ANN401
    """Format a dictionary of items.

    Args:
        mapping (dict[str, T]): The items to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.
        mode (int): The format mode. Defaults to FormatMode.NONE.
        valtype (ValType[T] | None): The expected type of the
            result. Defaults to object.

    Returns:
        Any: The formatted items.

    """
    formatted: dict[str, str | T] = {}
    for key, value in mapping.items():
        if isinstance(value, list):
            formatted[key] = cast(
                "str | T",
                format_list(cast("Iterable[Any]", value), fmt=fmt, mode=mode),
            )
        elif isinstance(value, dict):
            formatted[key] = cast(
                "str | T",
                format_dict(cast("dict[str, Any]", value), fmt=fmt, mode=mode),
            )
        else:
            formatted[key] = cast(
                "str | T",
                format_str(value, fmt=fmt, mode=mode),
            )

    type_assert(formatted, valtype)

    return formatted


def format_auto[T](
    item: T,
    *,
    fmt: dict[str, Any] | None = None,
    mode: int = FormatMode.NONE,
    valtype: ValType[T] = object,
) -> Any:  # noqa: ANN401
    """Format an item automatically.

    Args:
        item (T): The item to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.
        mode (int): The format mode. Defaults to FormatMode.NONE.
        valtype (ValType[T] | None): The expected type of the
            result. Defaults to object.

    Returns:
        Any: The formatted item.

    """
    if isinstance(item, list):
        return format_list(
            cast("Iterable[Any]", item),
            fmt=fmt,
            mode=mode,
            valtype=valtype,
        )
    if isinstance(item, dict):
        return format_dict(
            cast("dict[str, Any]", item),
            fmt=fmt,
            mode=mode,
            valtype=valtype,
        )
    return format_str(
        item,
        fmt=fmt,
        mode=mode,
        valtype=valtype,
    )
