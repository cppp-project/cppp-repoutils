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

"""Rubisco source package builder command events."""

from pathlib import Path
from typing import Any, cast

from rubisco.shared.api.archive import compress
from rubisco.shared.api.cefs import (
    Argument,
    DynamicArguments,
    EventCallback,
    EventFileData,
    EventPath,
    Option,
    load_callback_args,
)
from rubisco.shared.api.kernel import load_project_config
from rubisco.shared.api.l10n import _
from rubisco.shared.api.utils import rm_recursive
from rubisco.shared.api.variable import format_str

from cppp_srcpkg.dist import dist

__all__ = ["mount_to_cefs"]


def on_dist(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Fetch git extension."""
    opts, args_ = load_callback_args(options, args)

    archive_type = str(opts.get("archive-type")).split("+")
    archive_type = [x for x in archive_type if x]
    keep_srcdir = opts.get("keep-source-directory")
    name_format = format_str(opts.get("name-format"))
    dest = Path(cast("str", opts.get("destination")))
    src = Path(args_[0]) if len(args) > 0 else Path()

    if "none" in archive_type or not archive_type:
        keep_srcdir = True
        archive_type = []

    if "all" in archive_type:
        archive_type = ["zip", "tar.gz", "tar.bz2", "tar.xz"]

    # Build source directory.
    dest_dir = dest / cast("str", name_format)
    project_config = load_project_config(src)
    dist(src, dest_dir, project_config)

    # Build source archive.
    for ar_type in archive_type:
        archive_path = dest / (cast("str", name_format) + "." + ar_type)
        compress(
            dest_dir,
            archive_path,
            start=dest_dir.parent,
            compress_type=ar_type,
            compress_level=9,
            overwrite=True,
        )

    # Remove source directory.
    if not keep_srcdir:
        rm_recursive(dest_dir)

def mount_to_cefs() -> None:
    """Mount cefs events."""
    EventPath("/srcdist").mkfile(
            EventFileData(
                args=DynamicArguments(
                    name="srcdir",
                    title=_("Source directory"),
                    description=_("Source directory."),
                    mincount=0,
                    maxcount=1,
                ),
                callbacks=[
                    EventCallback(
                        callback=on_dist,
                        description=_("Make source package."),
                    ),
                ],
            ),
            description=_("Make source package."),
            options=[
                Option[str](
                    name="destination",
                    title=_("Destination"),
                    typecheck=str,
                    aliases=["d"],
                    description=_("Destination directory."),
                    default="dist",
                ),
                Option[str](
                    name="archive-type",
                    title=_("Archive type"),
                    typecheck=str,
                    aliases=["t"],
                    description=_(
                        "Archive type of the source distribution. Use '+' "
                        "to make different archives. e.g. 'zip+tar.gz'. "
                        "Use 'all' to select all supported types. Use "
                        "'none' to generate a directory instead of a "
                        "archive. Defaults to 'all'.",
                    ),
                    default="all",
                ),
                Option[bool](
                    name="keep-source-directory",
                    title=_("Keep source directory"),
                    typecheck=bool,
                    aliases=["k"],
                    description=_(
                        "Keep source directory. If `archive-type` is 'none', "
                        "this option will be enabled. Defaults to 'false'.",
                    ),
                    default=False,
                ),
                Option[str](
                    name="name-format",
                    title=_("Name format"),
                    typecheck=str,
                    aliases=["f"],
                    description=_(
                        "package name format. Defaults to '<project-name>-"
                        "<version>'",
                    ),
                    default="${{ project.name }}-${{ project.version }}",
                ),
            ],
        )
