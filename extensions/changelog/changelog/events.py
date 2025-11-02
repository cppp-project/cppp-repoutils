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

"""Rubisco subpackage manager command events."""

from pathlib import Path
from typing import Any

from rubisco.shared.api.cefs import (
    Argument,
    DynamicArguments,
    EventCallback,
    EventFileData,
    EventPath,
    Option,
    load_callback_args,
)
from rubisco.shared.api.l10n import _

from changelog.generator import gen_project_changelog

__all__ = ["mount_to_cefs"]


def on_changelog(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Output metadata."""
    _opts, args_ = load_callback_args(options, args)
    output = Path(str(_opts.get("output")))
    repo = Path().cwd() if len(args_) == 0 else Path(args_[0])
    gen_project_changelog(repo, output)


def mount_to_cefs() -> None:
    """Mount cefs events."""
    EventPath("/changelog").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="repo",
                title=_("Repository path."),
                description=_("Repository path."),
                mincount=0,
                maxcount=1,
            ),
            callbacks=[
                EventCallback(
                    callback=on_changelog,
                    description=_("Generate changelog."),
                ),
            ],
        ),
        options=[
            Option[str](
                name="output",
                title=_("Changelog file."),
                aliases=["o"],
                description=_("Path to save the generated changelog."),
                typecheck=str,
                default="ChangeLog",
            ),
        ],
        description=_("Generate changelog."),
    )
