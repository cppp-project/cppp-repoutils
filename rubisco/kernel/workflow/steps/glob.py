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

"""CopyFileStep implementation."""

import glob
from pathlib import Path
from typing import cast

from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.variable import push_variables
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["GlobFileStep"]


class GlobFileStep(Step):  # pylint: disable=R0902
    """Glob files or directories."""

    patterns: list[str]
    exclude_patterns: list[str]
    save_to: str | None
    root_dir: str | None
    recursive: bool
    include_hidden: bool
    include_regular_files: bool
    include_directories: bool
    include_symlinks: bool
    include_hardlinks: bool
    include_fifos: bool
    include_sockets: bool
    include_block_devices: bool
    include_char_devices: bool
    include_mountpoints: bool

    def init(self) -> None:
        """Initialize the step."""
        patterns = cast(
            "list[str]",
            format_auto(
                self.raw_data["glob"],
                mode=FormatMode.EXECUTE,
                valtype=str | list,
            ),
        )
        exclude_patterns = cast(
            "list[str]",
            format_auto(
                self.raw_data.get("excludes", []),
                mode=FormatMode.EXECUTE,
                valtype=str | list,
            ),
        )

        self.patterns = [patterns] if isinstance(patterns, str) else patterns

        self.exclude_patterns = (
            [exclude_patterns]
            if isinstance(
                exclude_patterns,
                str,
            )
            else exclude_patterns
        )

        self.root_dir = cast(
            "str | None",
            format_auto(
                self.raw_data.get("root", None),
                mode=FormatMode.EXECUTE,
                valtype=str | None,
            ),
        )
        self.save_to = cast(
            "str | None",
            format_auto(
                self.raw_data.get("save-to", None),
                mode=FormatMode.EXECUTE,
                valtype=str | None,
            ),
        )
        self.recursive = cast(
            "bool",
            format_auto(
                self.raw_data.get("recursive", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_hidden = cast(
            "bool",
            format_auto(
                self.raw_data.get("include-hidden", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_regular_files = cast(
            "bool",
            format_auto(
                self.raw_data.get("regular", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_directories = cast(
            "bool",
            format_auto(
                self.raw_data.get("dirs", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_symlinks = cast(
            "bool",
            format_auto(
                self.raw_data.get("symlinks", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_hardlinks = cast(
            "bool",
            format_auto(
                self.raw_data.get("hardlinks", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_directories = cast(
            "bool",
            format_auto(
                self.raw_data.get("dirs", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_symlinks = cast(
            "bool",
            format_auto(
                self.raw_data.get("symlinks", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_hardlinks = cast(
            "bool",
            format_auto(
                self.raw_data.get("hardlinks", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_fifos = cast(
            "bool",
            format_auto(
                self.raw_data.get("fifos", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_sockets = cast(
            "bool",
            format_auto(
                self.raw_data.get("sockets", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_block_devices = cast(
            "bool",
            format_auto(
                self.raw_data.get("block-devices", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        self.include_char_devices = cast(
            "bool",
            format_auto(
                self.raw_data.get("char-devices", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        devices = cast(
            "bool",
            format_auto(
                self.raw_data.get("devices", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )
        if devices:
            self.include_block_devices = True
            self.include_char_devices = True
        self.include_mountpoints = cast(
            "bool",
            format_auto(
                self.raw_data.get("mountpoints", True),
                mode=FormatMode.EXECUTE,
                valtype=bool,
            ),
        )

    def _need_ignore(self, path: Path) -> bool:
        return not (
            (self.include_regular_files and path.is_file())
            or (self.include_directories and path.is_dir())
            or (self.include_symlinks and path.is_symlink())
            or (self.include_hardlinks and path.stat().st_nlink > 1)
            or (self.include_fifos and path.is_fifo())
            or (self.include_sockets and path.is_socket())
            or (self.include_block_devices and path.is_block_device())
            or (self.include_char_devices and path.is_char_device())
            or (self.include_mountpoints and path.is_mount())
        )

    def run(self) -> None:
        """Run the step."""
        selected: list[Path] = []
        for pattern in self.patterns:
            selected.extend(
                [
                    Path(src).absolute()
                    for src in glob.glob(  # noqa: PTH207
                        pattern,
                        root_dir=self.root_dir,
                        recursive=self.recursive,
                        include_hidden=self.include_hidden,
                    )
                ],
            )
        excludes: list[Path] = []
        for pattern in self.exclude_patterns:
            excludes.extend(
                [
                    Path(src).absolute()
                    for src in glob.glob(  # noqa: PTH207
                        pattern,
                        root_dir=self.root_dir,
                        recursive=self.recursive,
                        include_hidden=self.include_hidden,
                    )
                ],
            )
        res: list[Path] = []
        res.extend(
            [
                p
                for p in selected
                if p.absolute() not in excludes and not self._need_ignore(p)
            ],
        )
        for path in res:
            call_ktrigger(
                IKernelTrigger.on_file_selected,
                path=path,
            )
        if self.save_to:
            push_variables(self.save_to, res)
        push_variables(f"{self.global_id}.files", res)
