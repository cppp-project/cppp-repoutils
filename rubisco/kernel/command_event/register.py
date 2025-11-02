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


"""Rubisco command event register module.

This module provides utilities for registering command events.
"""

from dataclasses import dataclass

from rubisco.kernel.command_event.cmd_event import EventObject
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
)
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str

__all__ = ["EventUnit", "register_events"]


@dataclass(frozen=True)
class EventUnit:
    """Util class for developer to register events."""

    name: str
    stat: EventObjectStat
    children: list["EventUnit"] | None = None
    file_data: EventFileData | None = None

    def __post_init__(self) -> None:
        """Check if the values are valid."""
        if self.stat.type is not EventObjectType.FILE and self.file_data:
            raise RUValueError(
                fast_format_str(
                    _("You can only register callbacks to files."),
                ),
            )

        if (
            self.stat.type == EventObjectType.FILE  # File's callback is data.
            and not self.file_data
        ):
            raise RUValueError(
                fast_format_str(
                    _("You must register callbacks to files."),
                ),
            )


def _register_events(
    event: EventUnit,
    root: EventObject,
) -> None:
    logger.info("Registering event %s to %s", event.name, root.abspath)
    if event.stat.type == EventObjectType.DIRECTORY:
        self = root.get_child(event.name)
        if self is None:
            self = root.add_child(event.name, event.stat)
        if event.children is not None:
            for child in event.children:
                _register_events(child, self)
    elif event.stat.type == EventObjectType.FILE:
        obj = root.add_child(event.name, event.stat)
        obj.file_data = event.file_data
    else:
        root.add_child(event.name, event.stat)


def register_events(
    events: list[EventUnit],
    root: EventPath | None = None,
) -> None:
    """Register events recursively to the event tree.

    Args:
        events ( list[EventUnit]): The event to register.
        root (EventPath | None): The root of the event tree. None means
            the root of the event tree. Defaults to None.

    """
    if root is None:
        root = EventPath("/")
    for event in events:
        _register_events(event, root.event_object)
