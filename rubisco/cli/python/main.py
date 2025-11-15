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

"""Rubisco Python interpreter wrapper."""

import atexit
import sys
from typing import Any

import colorama
import IPython

from rubisco.kernel.command_event.args import (
    Argument,
    Option,
    load_callback_args,
)


def on_exit() -> None:
    """Reset terminal color."""
    sys.stdout.write(colorama.Fore.RESET)
    sys.stdout.flush()


atexit.register(on_exit)


def main(
    options: list[Option[Any]],
    args: list[Argument[Any]],
) -> None:
    """Rubisco Python interpreter wrapper main entry point."""
    _, args_ = load_callback_args(options, args)

    colorama.init()
    IPython.start_ipython(argv=args_)  # type: ignore[type-arg]
