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

"""Checks if the file is ignored or included."""

import os
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from pygit2 import Repository
from rubisco.shared.api.log import rubisco_get_logger

from cppp_srcpkg.preprocessor import rubiscoignore_pre_process

if TYPE_CHECKING:
    from pygit2._pygit2 import GitError
else:
    from pygit2 import GitError

__all__ = ["RUBISCO_INCLUDE_FILE", "Manifest"]


RUBISCO_INCLUDE_FILE = ".rubisco/includes"

logger = rubisco_get_logger("cppp-srcpkg")


class Manifest:
    """Manifest for generate source dist package."""

    include_patterns: list[str]
    repo: Repository | None
    root: Path

    def __init__(self, root: Path) -> None:
        """Init a manifest.

        Args:
            root (Path): The working directory.

        """
        try:
            self.repo = Repository(str(root))
        except GitError:
            logger.warning("Error while loading git repository.", exc_info=True)
            self.repo = None

        if (root / RUBISCO_INCLUDE_FILE).exists():
            self.include_patterns = rubiscoignore_pre_process(
                root / RUBISCO_INCLUDE_FILE,
            )
        else:
            self.include_patterns = []

        self.root = Path(os.path.normpath(root.absolute()))

    def need_ignore(self, file: Path) -> bool:
        """Check for the file need ignore.

        Args:
            file (Path): The current file.

        Returns:
            bool: Return True if the file need ignore.

        """
        filepath = file.relative_to(self.root) if file.is_absolute() else file
        for pattern in self.include_patterns:
            if fnmatch(str(filepath), pattern):
                return False

        if self.repo is None:
            return False

        return bool(self.repo.path_is_ignored(str(filepath)))

    def get_patterns(self) -> list[str]:
        """Get patterns list.

        Returns:
            list[str]: patterns list.

        """
        return self.include_patterns
