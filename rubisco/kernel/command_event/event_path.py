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

"""Event path.

Event path is a path object that represents an event with CommandEvent
filesystem support.
"""

import os
import posixpath
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, Self

from rubisco.kernel.command_event.args import Option
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
)
from rubisco.kernel.command_event.root import get_root
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty

if TYPE_CHECKING:
    from _typeshed import StrPath

    from rubisco.kernel.command_event.cmd_event import EventObject

__all__ = ["EventPath"]


class EventPath(PurePosixPath):  # pylint: disable=R0904
    """A path object that represents an event.

    See `EventObject` for more information.
    """

    _event: "EventObject | None" = None

    def __new__(cls, *args: "StrPath") -> Self:
        """Initialize the EventPath class.

        Args:
            *args: The arguments to pass to the super class.

        Returns:
            Self: The instance of the class.

        """
        if args and not str(args[0]).startswith("/"):
            args = ("/" + str(args[0]), *args[1:])
        return super().__new__(cls, *args)

    def __eq__(self, other: object) -> bool:
        """Compare two EventPath.

        Args:
            other (object): The other EventPath.

        Returns:
            bool: True if equal, False otherwise.

        """
        if isinstance(other, str):
            return self.as_posix() == other
        if not isinstance(other, EventPath):
            return False
        return self.as_posix() == other.as_posix()

    def __hash__(self) -> int:
        """Get the hash of the event.

        Returns:
            int: The hash of the event.

        """
        return hash(self.as_posix())

    @property
    def event_object(self) -> "EventObject":
        """Get the event."""
        return self._get_event()

    def add_dir_callback(
        self,
        callback: EventCallback,
    ) -> None:
        """Add a callback to the event.

        Args:
            callback (EventCallback): The callback to add. It will be called
                when the directory's children files are executed.

        """
        _event = self.resolve().event_object
        if _event.stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("Not a directory: ${{path}}."),
                    fmt={
                        "path": self.as_posix(),
                    },
                ),
            )
        _event.stat().dir_callbacks.append(callback)

    def normpath(self) -> "EventPath":
        """Normalize the path."""
        return EventPath(posixpath.normpath(self.as_posix()))

    def _get_event(self) -> "EventObject":
        if self._event is not None:
            return self._event

        parts = self.normpath().parts[1:]
        if not parts:  # Root.
            return get_root()
        node = get_root()
        for part in parts:
            node = node.get_child(part)
            if node is None:
                raise RUValueError(
                    fast_format_str(
                        _("No such event: ${{path}}."),
                        fmt={
                            "path": self.as_posix(),
                        },
                    ),
                )
        self._event = node
        return node

    def stat(self) -> "EventObjectStat":
        """Get the stat of the event."""
        return self._get_event().stat()

    def list_dirs(self) -> list["EventPath"]:
        """List all directories of the event."""
        dirs = self.resolve().event_object.list_dirs()
        return [(self / part.name) for part in dirs]

    def list_files(self) -> list["EventPath"]:
        """List all files of the event."""
        files = self.resolve().event_object.list_files()
        return [(self / part.name) for part in files]

    def list_aliases(self) -> list["EventPath"]:
        """List all aliases of the event."""
        aliases = self.resolve().event_object.list_aliases()
        return [(self / part.name) for part in aliases]

    def list_mount_points(self) -> list["EventPath"]:
        """List all mount points of the event."""
        mount_points = self.resolve().event_object.list_mount_points()
        return [(self / part.name) for part in mount_points]

    def list_others(self) -> list["EventPath"]:
        """List all other types (not directories) of the event."""
        objs = self.resolve().event_object.list_others()
        return [(self / part.name) for part in objs]

    def iterpath(self) -> list["EventPath"]:
        """Get all children of the event."""
        objs = self.resolve().event_object.list_all()
        return [(self / part.name) for part in objs]

    def resolve(self) -> "EventPath":
        """Resolve the event."""
        if self._get_event().stat().type == EventObjectType.ALIAS:
            alias_to = self._get_event().stat().alias_to
            if alias_to is None:
                msg = "Alias to is None. This should not happen."
                raise AssertionError(msg)
            ep = EventPath(alias_to)
            return ep.resolve() if ep.exists() else ep
        return self

    def exists(self) -> bool:
        """Check if the event exists."""
        try:
            self.resolve().event_object.stat()
            return True  # noqa: TRY300
        except RUValueError:
            return False

    def is_dir(self) -> bool:
        """Check if the event is a directory."""
        if not self.exists():
            return False
        obj = self.resolve().event_object
        return obj.stat().type == EventObjectType.DIRECTORY

    def is_file(self) -> bool:
        """Check if the event is a file."""
        if not self.exists():
            return False
        obj = self.resolve().event_object
        return obj.stat().type == EventObjectType.FILE

    def is_alias(self) -> bool:
        """Check if the event is an alias."""
        if not self.exists():
            return False
        obj = self.resolve().event_object
        return obj.stat().type == EventObjectType.ALIAS

    def is_mount_point(self) -> bool:
        """Check if the event is a mount point."""
        if not self.exists():
            return False
        obj = self.resolve().event_object
        return obj.stat().type == EventObjectType.MOUNT_POINT

    def is_other(self) -> bool:
        """Check if the event is other types (not a directory)."""
        if not self.exists():
            return False
        obj = self.resolve().event_object
        return obj.stat().type in {
            EventObjectType.FILE,
            EventObjectType.ALIAS,
            EventObjectType.MOUNT_POINT,
        }

    def read(self) -> EventFileData | None:
        """Read the file data of the event."""
        obj = self.resolve().event_object
        return obj.file_data

    def execute(self, args: list[str]) -> None:
        """Execute the event."""
        self.resolve().event_object.execute(args)

    def set_option(
        self,
        name: str,
        value: Any,  # noqa: ANN401
    ) -> Self:
        """Set an option of the event.

        Args:
            name (str): The name of the option.
            value (Any): The value of the option.

        Returns:
            Self: Self.

        """
        self.resolve().event_object.set_option(name, value)
        return self

    def _get_parent(self) -> "EventPath":
        parent = EventPath(self.parent).resolve()
        if not parent.exists():
            raise RUValueError(
                fast_format_str(
                    _("No such event: ${{path}}."),
                    fmt={
                        "path": make_pretty(self.parent.as_posix()),
                    },
                ),
                hint=_(
                    "Rubisco command event filesystem does not support "
                    "recursive creation of directories. You must create "
                    "the parent directory first because you must set the "
                    "description explicitly.",
                ),
            )
        if parent.stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("Not a directory: ${{path}}."),
                    fmt={
                        "path": make_pretty(self.parent.as_posix()),
                    },
                ),
            )
        return parent

    def mkdir(
        self,
        description: str,
        options: list[Option[Any]] | None = None,
        callback: EventCallback | list[EventCallback] | None = None,
        *,
        exists_ok: bool = True,
    ) -> Self:
        """Create a directory.

        Args:
            description (str): The description of the directory.
            options (list[Option] | None, optional): The options of the
                directory. Defaults to None.
            callback (EventCallback | list[EventCallback] | None, optional): The
                callback of the directory. Defaults to None. It will be called
                when the directory's children files are executed.
            exists_ok (bool): If True, do nothing if the directory already
                exists.

        Returns:
            Self: Self.

        """
        if self.exists():
            if not exists_ok:
                raise RUValueError(
                    fast_format_str(
                        _("File exists: ${{path}}"),
                        fmt={
                            "path": make_pretty(self.as_posix()),
                        },
                    ),
                )
            return self
        logger.info(
            "Creating directory %s with description %s",
            self.as_posix(),
            description,
        )
        parent = self._get_parent()
        self._event = parent.event_object.add_child(
            self.name,
            EventObjectStat(
                type=EventObjectType.DIRECTORY,
                options=options or [],
                description=description,
                dir_callbacks=(
                    []
                    if callback is None
                    else callback
                    if isinstance(callback, list)
                    else [callback]
                ),
            ),
        )
        return self

    def mkfile(
        self,
        data: EventFileData,
        options: list[Option[Any]] | None = None,
        description: str | None = None,
    ) -> Self:
        """Create a command event file.

        Args:
            data (EventFileData): The data of the file.
            options (list[Option] | None, optional): The options of the file.
                Defaults to None.
            description (str | None, optional): The description of the file.
                Defaults to None.

        Returns:
            Self: Self.

        """
        if self.exists():
            raise RUValueError(
                fast_format_str(
                    _("File exists: ${{path}}"),
                    fmt={
                        "path": make_pretty(self.as_posix()),
                    },
                ),
            )
        logger.info(
            "Creating file %s with data %s",
            self.as_posix(),
            data,
        )
        parent = self._get_parent()
        self._event = parent.event_object.add_child(
            self.name,
            EventObjectStat(
                type=EventObjectType.FILE,
                options=options or [],
                description=description,
            ),
        )
        self._event.write(data)
        return self

    def update_file(
        self,
        data: EventFileData,
        options: list[Option[Any]] | None = None,
        description: str | None = None,
    ) -> Self:
        """Update a file's callback if it exists. Otherwise, create a new file.

        Args:
            data (EventFileData): The callback to merge.
            options (list[Option[Any]] | None, optional): The options of the
                file. **ONLY ACTIVE IF THE FILE NOT EXISTS.** Defaults to None.
            description (str | None, optional): The description of the file.
                **ONLY ACTIVE IF THE FILE NOT EXISTS.** Defaults to None.

        Returns:
            Self: Self.

        """
        if self.exists():
            file_data = self.resolve().event_object.file_data
            if not file_data:
                raise RUValueError(
                    fast_format_str(
                        _("Not a file: ${{path}}"),
                        fmt={"path": self.as_posix()},
                    ),
                )
            file_data.merge(data)
        else:
            self.mkfile(data, options, description)
        return self

    def mklink(self, alias_to: str | os.PathLike[str]) -> Self:
        """Create a link.

        Args:
            alias_to (str | PathLike[str]): The path to link to.

        Returns:
            Self: Self.

        """
        if self.exists():
            raise RUValueError(
                fast_format_str(
                    _("File exists: ${{path}}"),
                    fmt={
                        "path": make_pretty(self.as_posix()),
                    },
                ),
            )
        logger.info(
            "Creating link %s to %s",
            self.as_posix(),
            alias_to,
        )
        parent = self._get_parent()
        self._event = parent.event_object.add_child(
            self.name,
            EventObjectStat(
                type=EventObjectType.ALIAS,
                alias_to=alias_to,
            ),
        )
        return self

    def mount(self, mount_to: str) -> Self:
        """Make a mount point.

        Args:
            mount_to (str): The shell command to mount.

        Returns:
            Self: Self.

        """
        if self.exists():
            raise RUValueError(
                fast_format_str(
                    _("File exists: ${{path}}"),
                    fmt={
                        "path": make_pretty(self.as_posix()),
                    },
                ),
            )
        logger.info(
            "Creating mount point %s with command %s",
            self.as_posix(),
            mount_to,
        )

        parent = self._get_parent()
        self._event = parent.event_object.add_child(
            self.name,
            EventObjectStat(
                type=EventObjectType.MOUNT_POINT,
                mount_to=mount_to,
            ),
        )
        return self

    def __repr__(self) -> str:
        """Return a string representation of the event."""
        return f"EventPath({self.as_posix()!r})"
