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

"""Generate command line."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import beartype

__all__ = ["command", "expand_cmdlist"]


_T = Iterable  # Make Ruff happy.


@beartype.beartype
def command(args: Iterable[Any] | str) -> str:
    """Generate shell command from a list of arguments.

    Args:
        args (Iterable[Any] | str): The list of arguments.

    Returns:
        str: The shell command.

    """
    if isinstance(args, str):
        return args
    args = expand_cmdlist(args)

    res_command = ""
    for arg in args:
        if " " in arg:
            if '"' in arg:
                arg = arg.replace('"', '\\"')  # noqa: PLW2901
            res_command += f'"{arg}" '
        else:
            res_command += f"{arg} "
    return res_command.strip()


def expand_cmdlist(args: Iterable[str | Iterable[Any]]) -> list[str]:
    """Expand recursive command list to flat list.

    Args:
        args (Iterable[str | Iterable[Any]]): The list of arguments.

    Returns:
        list[str]: The flat list of arguments.

    """
    res_args: list[str] = []
    for arg in args:
        if isinstance(arg, list):
            res_args.extend(expand_cmdlist(arg))
        else:
            res_args.append(str(arg))
    return res_args
