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

"""Rubisco event object.

Event object is internal object for a event. It's like a object in file system.
"""

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

from rubisco.kernel.command_event.args import Argument, DynamicArguments
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
from rubisco.lib.variable.utils import make_pretty

__all__ = ["EventObject"]


class EventObject:
    """A command event tree node.

    The event tree is structured similarly to a filesystem tree. The root
    represents the command `ru`, with its children nodes representing
    subcommands and its leaves representing events. For example, if the command
    `ru ext show -w` is called, the event tree would look like this:

    ```
    ru                              --- ROOT
    ├── ext                         --- EventTree
    │   └── show --> {"-w": True}   --- Event
    ```

    You can also use an alias to register an event. It is like a symlink in a
    filesystem. For example, adding an alias `/ext` to `/extension` results in
    the following event tree:

    ```
    ru                              --- ROOT
    ├── ext                         --- EventTree
    │   ├── show --> {"-w": True}   --- Event
    ├── extension --> /ext          --- EventTree (alias)
    │   └── show --> {"-w": True}   --- Event (Same as /ext/show)
    ```

    We also support "export" and "mount."

    **Export** can export a command to the system path. For example, exporting
    `/ext` as `ruext` in the system path makes the command `ruext show -w`
    equivalent to `ru ext show -w`.

    **Mount** can import a command from the system path. It is an automatic
    operation. We automatically import all commands that start with `ru-` or
    `rubisco-` in the system path. For example, if you have a command `ru-make`
    in the system path, it will be imported to `/make`. Executing `ru make -h`
    will then be equivalent to `ru-make -h`.

    However, if `/make` already exists in the command tree, it will be ignored.
    This is to prevent users from overriding built-in or extension commands.
    """

    abspath: PurePosixPath
    parent: "EventObject | None"
    name: str
    _stat: EventObjectStat

    # File data.
    file_data: EventFileData | None = None

    @dataclass
    class _Childrens:  # pylint: disable=R0903
        dirs: dict[str, "EventObject"] = field(
            default_factory=dict[str, "EventObject"],
        )
        files: dict[str, "EventObject"] = field(
            default_factory=dict[str, "EventObject"],
        )
        aliases: dict[str, "EventObject"] = field(
            default_factory=dict[str, "EventObject"],
        )
        mount_points: dict[str, "EventObject"] = field(
            default_factory=dict[str, "EventObject"],
        )

    children: _Childrens

    _resolved_aliases: "EventObject | None" = None

    def __init__(  # pylint: disable=R0913
        self,
        name: str,
        parent: "EventObject | None",
        stat: EventObjectStat,
        abspath: PurePosixPath,
        *,
        file_data: EventFileData | None = None,
    ) -> None:
        """Initialize an command event tree node.

        Args:
            name (str): The name of the node.
            parent (EventObject | None): The parent of the node.
            stat (EventObjectStat): The stat of the node.
            abspath (PurePosixPath): The absolute path of the node.
            file_data (EventFileData | None): The file data of the node.

        """
        self.name = name
        self.parent = parent
        self._stat = stat
        self.abspath = abspath
        self.children = EventObject._Childrens()
        self.file_data = file_data

    def stat(self) -> EventObjectStat:
        """Get the stat of the node.

        Returns:
            EventObjectStat: The stat of the node.

        """
        return self._stat

    def set_stat(self, stat: EventObjectStat) -> None:
        """Set the stat of the node.

        Args:
            stat (EventObjectStat): The stat of the node.

        """
        self._stat = stat

    def add_child(
        self,
        name: str,
        stat: EventObjectStat,
    ) -> "EventObject":
        """Add a child to the node.

        Args:
            name (str): The name of the child.
            stat (EventObjectStat): The stat of the child.

        Returns:
            EventObject: The child of the node.

        """
        logger.debug(
            "Adding EventObject child %s to %s",
            name,
            self.resolve_alias().abspath,
        )
        path = self.resolve_alias().abspath / name
        child = EventObject(name, self, stat, abspath=path)
        if stat.type == EventObjectType.DIRECTORY:
            self.resolve_alias().children.dirs[name] = child
            return child
        if stat.type == EventObjectType.FILE:
            self.resolve_alias().children.files[name] = child
            return child
        if stat.type == EventObjectType.ALIAS:
            self.resolve_alias().children.aliases[name] = child
            return child
        if stat.type == EventObjectType.MOUNT_POINT:
            self.resolve_alias().children.mount_points[name] = child
            return child
        msg = "Invalid type for EventObject."
        raise TypeError(msg)

    def get_child(self, name: str) -> "EventObject | None":
        """Get a child of the node.

        Args:
            name (str): The name of the child.

        Returns:
            EventObject | None: The child of the node. If the child does not
            exist, return None.

        """
        return (
            self.resolve_alias().children.dirs.get(name)
            or self.resolve_alias().children.files.get(name)
            or self.resolve_alias().children.aliases.get(name)
            or self.resolve_alias().children.mount_points.get(name)
        )

    def list_dirs(self) -> list["EventObject"]:
        """List all directories of the node.

        Returns:
            list[EventObject]: All directories of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return list(self.resolve_alias().children.dirs.values())

    def list_files(self) -> list["EventObject"]:
        """List all files of the node.

        Returns:
            list[EventObject]: All files of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return list(self.resolve_alias().children.files.values())

    def list_aliases(self) -> list["EventObject"]:
        """List all aliases of the node.

        Returns:
            list[EventObject]: All aliases of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return list(self.resolve_alias().children.aliases.values())

    def list_mount_points(self) -> list["EventObject"]:
        """List all mount points of the node.

        Returns:
            list[EventObject]: All mount points of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return list(self.resolve_alias().children.mount_points.values())

    def list_others(self) -> list["EventObject"]:
        """List all other types (not directories) of the node.

        Returns:
            list[EventObject]: All other types of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return (
            list(self.resolve_alias().children.files.values())
            + list(self.resolve_alias().children.aliases.values())
            + list(self.resolve_alias().children.mount_points.values())
        )

    def list_all(self) -> list["EventObject"]:
        """Get all children of the node.

        Returns:
            list[EventObject]: All children of the node.

        """
        if self.resolve_alias().stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a event directory."),
                    fmt={
                        "name": self.resolve_alias().abspath,
                    },
                ),
            )
        return (
            list(self.resolve_alias().children.dirs.values())
            + list(self.resolve_alias().children.files.values())
            + list(self.resolve_alias().children.aliases.values())
            + list(self.resolve_alias().children.mount_points.values())
        )

    def has_dir(self, name: str) -> bool:
        """Check if the node has a directory.

        Args:
            name (str): The name of the directory.

        Returns:
            bool: True if the node has the directory, False otherwise.

        """
        return name in self.resolve_alias().children.dirs

    def resolve_alias(self) -> "EventObject":
        """Resolve the alias of the node.

        Returns:
            EventObject: The resolved node.

        """
        if self._resolved_aliases is None:
            if self._stat.type != EventObjectType.ALIAS:
                return self
            if self._stat.alias_to is None:
                msg = "The alias is not set. This should never happen."
                raise AssertionError(msg)
            filepath = EventPath(self._stat.alias_to).resolve()
            self._resolved_aliases = filepath.event_object
        return self._resolved_aliases

    def set_option(
        self,
        name: str,
        value: Any,  # noqa: ANN401
    ) -> None:
        """Set an option of the node.

        Args:
            name (str): The name of the option.
            value (Any): The value of the option.

        """
        file_stat = self.resolve_alias().stat()

        for opt in file_stat.options:
            if opt.name == name or name in opt.aliases:
                opt.value = value
                break
        else:
            msg = fast_format_str(
                _("The option ${{name}} does not exist."),
                fmt={
                    "name": name,
                },
            )
            raise RUValueError(msg)

    def _execute_get_fileinfo(self) -> tuple[EventFileData, EventObjectStat]:
        resolved_object = self.resolve_alias()
        file_data = resolved_object.file_data
        file_stat = resolved_object.stat()
        if file_data is None:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{name}} is not a file."),
                    fmt={
                        "name": self.name,
                    },
                ),
            )
        return file_data, file_stat

    def _execute_dynamic_args(
        self,
        file_data_args: DynamicArguments,
        file_data: EventFileData,
        args: list[str],
    ) -> None:
        mincount = file_data_args.mincount
        maxcount = file_data_args.maxcount
        if mincount > len(args):
            msg = fast_format_str(
                _("The number of arguments is less than ${{mincount}}."),
                fmt={
                    "mincount": mincount,
                },
            )
            raise RUValueError(msg)
        if maxcount != -1 and len(args) > maxcount:
            msg = fast_format_str(
                _("The number of arguments is more than ${{maxcount}}."),
                fmt={
                    "maxcount": maxcount,
                },
            )
            raise RUValueError(msg)
        for callback in file_data.callbacks:
            compiled_args: list[Argument[Any]] = []
            for arg in args:
                compiled_arg = Argument[Any](
                    name=file_data_args.name,
                    title=file_data_args.title,
                    description=file_data_args.description,
                    typecheck=str,
                    default=None,
                )
                compiled_arg.value = arg
                compiled_args.append(compiled_arg)
            callback.callback(self._stat.options, compiled_args)

    def execute_dir(self) -> None:
        """Execute the directory.

        Raises:
            RUValueError: If the node is not a directory.

        """
        resolved_object = self.resolve_alias()

        # Execute parents.
        if resolved_object.parent is not None:
            resolved_object.parent.execute_dir()

        logger.info("Executing event directory %s ...", self.abspath)
        if resolved_object.stat().type != EventObjectType.DIRECTORY:
            raise RUValueError(
                fast_format_str(
                    _("Not a directory: ${{path}}."),
                    fmt={
                        "path": self.abspath,
                    },
                ),
            )

        try:
            for opt in resolved_object.stat().options:
                opt.get()  # Try to get the value to check if it's set.
                opt.freeze()
            for callback in resolved_object.stat().dir_callbacks:
                callback.callback(resolved_object.stat().options, [])
        finally:
            for opt in resolved_object.stat().options:
                opt.unfreeze()

    def execute(self, args: list[Any]) -> None:
        """Execute the node.

        Args:
            args (list[Any]): The arguments of the node.

        """
        logger.info("Executing event %s with args %s", self.abspath, args)
        file_data, file_stat = self._execute_get_fileinfo()

        for opt in file_stat.options:
            opt.get()  # Try to get the value to check if it's set.

        # Before execute the file, we should execute the parents.
        if self.parent is not None:
            self.parent.execute_dir()

        if isinstance(file_data.args, DynamicArguments):
            self._execute_dynamic_args(file_data.args, file_data, args)
            return

        if len(args) != len(file_data.args):
            raise RUValueError(
                fast_format_str(
                    _(
                        "The number of arguments is not correct. Expected "
                        "${{expected}}, got ${{got}}.",
                    ),
                    fmt={
                        "expected": len(file_data.args),
                        "got": len(args),
                    },
                ),
            )

        try:
            for idx, opt in enumerate(args):
                file_data.args[idx].value = opt
                file_data.args[idx].freeze()
                file_data.args[idx].get()  # Type check.
            for callback in file_data.callbacks:
                callback.callback(
                    self.resolve_alias().stat().options,
                    file_data.args,
                )
        finally:
            for arg in file_data.args:
                arg.unfreeze()

    def write(self, data: EventFileData) -> None:
        """Write the file data to the node.

        Args:
            data (EventFileData): The file data to write.

        """
        logger.info("Writing event '%s' with data %s", self.abspath, data)
        if self.resolve_alias().stat().type != EventObjectType.FILE:
            raise RUValueError(
                fast_format_str(
                    _("The node ${{path}} is not a file."),
                    fmt={
                        "path": make_pretty(self.abspath),
                    },
                ),
            )

        self.file_data = data

    def __repr__(self) -> str:
        """Return a string representation of the node."""
        return (
            f"EventObject(name={self.name!r}, abspath={self.abspath!r}"
            f", stat={self._stat!r})"
        )
