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

"""Rubisco CLI for CommandEventFS debugging."""

from typing import Any

from rubisco.cli.cefs_dbg.cli import RubiscoCEFSDebuggerCLI
from rubisco.cli.output import output_step
from rubisco.kernel.command_event.args import Argument, Option
from rubisco.lib.l10n import _

__all__ = ["cefs_callback"]


def cefs_callback(
    options: list[Option[Any]],  # noqa: ARG001 # pylint: disable=W0613
    args: list[Argument[Any]],  # noqa: ARG001 # pylint: disable=W0613
) -> None:
    """Launch Rubisco CommandEventFS Debugger CLI.

    Args:
        options (list[Option[Any]]): Options of command line.
        args (list[Argument[Any]]): Arguments of command line.

    """
    try:
        RubiscoCEFSDebuggerCLI().run()
    except (SystemExit, KeyboardInterrupt, EOFError):
        output_step(_("Rubisco CommandEventFS Debugger CLI exited."))
