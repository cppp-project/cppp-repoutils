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

"""RuBP packaging steps."""

from pathlib import Path

from rubisco.shared.api.kernel import Step, load_project_config
from rubisco.shared.api.variable import format_auto

from rubp_build.packaging import RuBP

__all__ = ["RUBPPackStep"]


class RUBPPackStep(Step):
    """RuBP packaging step."""

    srcdir: str
    bindir: str | None
    readme: str | None
    license_: str | None
    distdir: str | None
    version: str | None

    def init(self) -> None:
        """Init the step."""
        self.srcdir = format_auto(
            self.raw_data.get("srcdir", "."),
            valtype=str,
        )
        self.bindir = format_auto(
            self.raw_data.get("bindir", None),
            valtype=str | None,
        )
        self.readme = format_auto(
            self.raw_data.get("readme", None),
            valtype=str | None,
        )
        self.license_ = format_auto(
            self.raw_data.get("license", None),
            valtype=str | None,
        )
        self.distdir = format_auto(
            self.raw_data.get("distdir", None),
            valtype=str | None,
        )
        self.version = format_auto(
            self.raw_data.get("version", None),
            valtype=str | None,
        )

    def run(self) -> None:
        """Run the step."""
        config = load_project_config(Path(self.srcdir))
        rubp = RuBP(config.config)

        # If variables is not None, then override the variables in the config.
        if self.bindir is not None:
            rubp.bindir = Path(self.bindir)
        if self.readme is not None:
            rubp.readme = Path(self.readme)
        if self.license_ is not None:
            rubp.license = Path(self.license_)
        if self.distdir is not None:
            rubp.distdir = Path(self.distdir)
        if self.version is not None:
            rubp.version = self.version

        rubp.pack()
