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

"""Rubisco CommandEventFS root."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rubisco.kernel.command_event.cmd_event import EventObject

__all__ = ["get_root", "set_root"]

_root: "EventObject | None" = None  # pylint: disable=C0103


def set_root(root: "EventObject") -> None:
    """Set the root command event.

    Args:
        root (EventObject): The root command event.

    """
    global _root  # noqa: PLW0603 # pylint: disable=W0603
    _root = root


def get_root() -> "EventObject":
    """Get the root command event.

    Raises:
        AssertionError: If the root command event is not set.

    Returns:
        EventObject: The root command event.

    """
    if _root is None:
        msg = "Root command event is not set."
        raise AssertionError(msg)
    return _root
