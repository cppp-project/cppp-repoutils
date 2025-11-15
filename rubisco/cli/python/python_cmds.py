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

"""C++ Plus Rubisco extension manager command lines."""

from __future__ import annotations

from rubisco.cli.python.main import main as python_main
from rubisco.kernel.command_event.args import DynamicArguments
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.lib.l10n import _

__all__ = ["register_python_cmds"]


def register_python_cmds() -> None:
    """Register extension manager commands."""
    # Command "ext list".
    EventPath("/python").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="args",
                title=_("IPython arguments."),
                description=_("IPython arguments."),
                mincount=0,
            ),
            callbacks=[
                EventCallback(
                    callback=python_main,
                    description=_(
                        "Launch IPython interpreter.",
                    ),
                ),
            ],
        ),
        description=_(
            "Launch IPython interpreter. "
            "Use `/python -- [options] arguments` to pass arguments.",
        ),
        options=[],
    )
