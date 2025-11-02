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

"""Workflow steps for Rubisco subpackage manager."""

from pathlib import Path

from rubisco.shared.api.exception import RUValueError
from rubisco.shared.api.kernel import Step
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import fast_format_str, format_auto

from subpackages.package import SubpackageReference


class FetchStep(Step):
    """Fetch subpackages step."""

    url: str
    path: list[Path]
    branch: str
    protocol: str
    shallow: bool
    use_mirror: bool

    def init(self) -> None:
        """Initialize the step."""
        url: str | None = format_auto(
            self.raw_data.get("subpkg-fetch", None),
            valtype=str | None,
        )
        if url is None:
            raise RUValueError(
                fast_format_str(
                    _("Missing URL for fetching subpackages."),
                ),
            )
        self.url = url
        path = format_auto(
            self.raw_data.get("path", None),
            valtype=str | list[str] | None,
        )
        if path is None:
            raise RUValueError(
                fast_format_str(
                    _("Missing path for fetching subpackages."),
                ),
            )
        if isinstance(path, str):
            path = [Path(path)]
        else:
            path = [Path(p) for p in path]
        self.path = path

        self.branch = format_auto(
            self.raw_data.get("branch", "main"),
            valtype=str,
        )
        self.protocol = format_auto(
            self.raw_data.get("protocol", "http"),
            valtype=str,
        )
        self.shallow = format_auto(
            self.raw_data.get("shallow", True),
            valtype=bool,
        )
        self.use_mirror = format_auto(
            self.raw_data.get("use-mirror", True),
            valtype=bool,
        )

    def run(self) -> None:
        """Run the step."""
        pkg = SubpackageReference(
            name=self.url,
            branch=self.branch,
            url=self.url,
            paths=self.path,
        )
        pkg.fetch(
            protocol=self.protocol,
            shallow=self.shallow,
            use_direct=not self.use_mirror,
        )
