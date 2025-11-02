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

"""Rubisco variable system utilities."""

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, cast

from rubisco.lib.typecheck import is_instance

__all__ = ["iter_assert", "make_pretty", "merge_dict"]


def make_pretty(  # noqa: C901, PLR0912 # pylint: disable=R0912
    string: Path | str | Any,  # noqa: ANN401
    empty: str = "",
) -> str:
    """Make the path string pretty.

    Args:
        string (Path | str | Any): The string to get representation.
        empty (str): The string to return if the input is empty.

    Returns:
        str: Result string.

    """
    string_ = str(string)

    if not string:
        return empty

    if string_.endswith("\\"):
        string_ += "\\"

    if " " in string_:
        string_ = f"'{string_}'"

    strpath = Path(string)
    if strpath.exists():
        string_ = f"[underline]{string_}[/underline]"

    if strpath.is_dir() and not strpath.is_symlink():
        string_ = f"[magenta]{string_}[/magenta]"
    elif strpath.is_block_device() and not strpath.is_symlink():
        string_ = f"[yellow]{string_}[/yellow]"
    elif strpath.is_char_device() and not strpath.is_symlink():
        string_ = f"[on black][bright_yellow]{string_}[/][/]"
    elif strpath.is_socket() and not strpath.is_symlink():
        string_ = f"[on black][bright_magenta]{string_}[/][/]"
    elif strpath.is_fifo() and not strpath.is_symlink():
        string_ = f"[on black][bright_yellow]{string_}[/][/]"
    else:
        try:
            if strpath.is_symlink() and strpath.resolve().exists():
                string_ = f"[cyan]{string_}[/cyan]"
            elif strpath.is_symlink():
                string_ = f"[red]{string_}[/red]"
            elif strpath.lstat().st_mode & 0o100:
                string_ = f"[green]{string_}[/green]"
        except OSError:
            pass

    return string_


def iter_assert(
    iterable: Iterable[Any],
    checker: Callable[[Any], bool],
    exc: Exception | Callable[[Any], Exception],
) -> None:
    """Iterate the iterable and assert the elements.

    Args:
        iterable (Iterable[Any]): The iterable to iterate.
        checker (Callable[[Any], bool]): Element checker.
            The argument is the element in the iterable.
        exc (Exception | Callable[Any]): The exception to raise or the
            `on_error` callback. The argument is the element in the iterable.
            Returns the exception to raise.

    Raises:
        Exception: If the element does not pass the checker.

    """
    if is_instance(exc, Exception):
        exc_ = cast("Exception", exc)

        def _exc(
            e: Any,  # noqa: ARG001 ANN401 # pylint: disable=unused-argument
        ) -> Exception:
            return exc_

        exc = _exc

    for obj in iterable:
        if not checker(obj):
            raise cast("Callable[[Any], Exception]", exc)(obj)


def merge_dict(
    dst: dict[Any, Any],
    src: dict[Any, Any],
) -> None:
    """Merge two dicts.

    Args:
        dst (dict[Any, Any]): The first dict.
        src (dict[Any, Any]): The second dict.

    Returns:
        dict[Any, Any]: The merged dict.

    """
    for key, value in src.items():
        if key in dst:
            if isinstance(value, dict) and isinstance(dst[key], dict):
                merge_dict(dst[key], cast("dict[Any, Any]", value))
            elif isinstance(value, list) and isinstance(dst[key], list):
                cast("list[Any]", dst[key]).extend(cast("list[Any]", value))
            else:
                dst[key] = value
        else:
            dst[key] = value
