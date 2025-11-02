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

"""Rubisco command event callback."""

import traceback
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from rubisco.kernel.command_event.args import Argument, Option

__all__ = ["EventCallback", "EventCallbackFunction"]


@runtime_checkable
class EventCallbackFunction(Protocol):  # pylint: disable=R0903
    """Event callback protocol."""

    def __call__(
        self,
        options: list[Option[Any]],
        args: list[Argument[Any]],
    ) -> None:
        """Event callback function.

        Args:
            options (list[Option[Any]]): The options of the command.
            args (list[Argument[Any]]): The arguments of the command.

        """


@dataclass
class EventCallback:
    """Event callback."""

    callback: EventCallbackFunction
    description: str
    stacktrace: list[traceback.FrameSummary] | None = None  # For debug.

    def __post_init__(self) -> None:
        """Post init."""
        if self.stacktrace is None:
            self.stacktrace = list(traceback.extract_stack())[:-1]
