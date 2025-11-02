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

from rubisco.shared.api.kernel import Step
from rubisco.shared.api.variable import format_auto

from changelog.generator import gen_project_changelog

__all__ = ["ChangelogStep"]


class ChangelogStep(Step):
    """Changelog generation step."""

    path: Path
    repo: Path

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(
            format_auto(
                self.raw_data["changelog"],
                valtype=str,
            ),
        )
        self.repo = Path(
            format_auto(
                self.raw_data.get("repo", "."),
                valtype=str,
            ),
        )

    def run(self) -> None:
        """Run the step."""
        gen_project_changelog(self.repo, self.path)
