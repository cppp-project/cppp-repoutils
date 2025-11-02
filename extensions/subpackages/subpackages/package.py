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

"""Package class."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from rubisco.shared.api.exception import (
    RUNotRubiscoProjectError,
    RUTypeError,
    RUValueError,
)
from rubisco.shared.api.git import git_clone
from rubisco.shared.api.kernel import (
    ProjectConfigration,
    load_project_config,
)
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import fast_format_str, format_auto


@dataclass
class SubpackageReference:
    """Subpackage reference."""

    name: str
    branch: str
    url: str
    paths: list[Path]
    # We support multiple paths. If one of its path exists, we will use it.

    def exists(self) -> bool:
        """Check if the subpackage exists.

        Returns:
            bool: True if the subpackage exists.

        """
        return any(path.exists() for path in self.paths)

    def get_path(self) -> Path:
        """Get the path of the subpackage.

        Returns:
            Path: The path of the subpackage.

        """
        for path in self.paths:
            if path.exists():
                return path
        return self.paths[0]

    def fetch(
        self,
        protocol: str,
        *,
        shallow: bool = True,
        use_direct: bool = False,
    ) -> None:
        """Fetch the subpackage itself.

        Args:
            protocol (str): The protocol to use.
            shallow (bool, optional): Whether to use shallow clone. Defaults to
                True.
            use_direct (bool, optional): Whether to use direct url without
                mirror speed test. Defaults to False.

        Returns:
            Package | None: The fetched package.

        """
        path = self.get_path()
        if self.exists():
            return

        git_clone(
            self.url,
            path,
            branch=self.branch,
            protocol=protocol,
            shallow=shallow,
            use_fastest=not use_direct,
        )

    def fetch_subpackages(
        self,
        protocol: str,
        *,
        shallow: bool = True,
        use_direct: bool = False,
    ) -> "Package | None":
        """Fetch the subpackage's subpackages.

        Args:
            protocol (str): The protocol to use.
            shallow (bool, optional): Whether to use shallow clone. Defaults to
                True.
            use_direct (bool, optional): Whether to use direct url without
                mirror speed test. Defaults to False.

        Returns:
            Package | None: The fetched package.

        """
        path = self.get_path()
        if not path.exists():
            # fetch() should be called before this method. For BFS iteration.
            raise RUValueError(
                fast_format_str(
                    _("Subpackage ${{name}} does not exist."),
                    fmt={"name": self.name},
                ),
                hint=_("Please fetch the subpackage ITSELF first."),
            )

        try:
            pkg = Package(path)
            pkg.fetch(
                protocol=protocol,
                shallow=shallow,
                use_direct=use_direct,
            )
        except RUNotRubiscoProjectError:
            return None
        return pkg


class Package:
    """Package class."""

    name: str
    path: Path
    config: ProjectConfigration
    subpackage_refs: list[SubpackageReference]
    subpackages: "list[Package | None]"

    def __init__(self, path: Path) -> None:
        """Parse a rubisco package.

        Args:
            path (Path): The path of the package.

        """
        config = load_project_config(path)
        self.name = config.name
        self.path = path
        self.config = config
        self._load_subpkg_refs()
        self._load_subpackages()

    def _load_subpkg_refs(self) -> None:
        subpkgs: list[SubpackageReference] = []
        subpkg_dict: dict[str, object] = format_auto(
            self.config.config.config.get("subpackages", {}),
            valtype=dict,
        )
        for name, subpkg_ in subpkg_dict.items():
            if not isinstance(subpkg_, dict):  # type: ignore[union-attr]
                msg = fast_format_str(
                    _("Subpackage reference ${{name}} is not a dict."),
                    fmt={"name": name},
                )
                raise RUTypeError(msg)
            subpkg = cast("dict[str, object]", subpkg_)
            branch: str = format_auto(
                subpkg.get("branch", "main"),
                valtype=str,
            )
            url: str = format_auto(subpkg["url"], valtype=str)
            paths: list[str] | str = format_auto(
                subpkg.get("path", []),
                valtype=list[str] | str,
            )
            if isinstance(paths, str):
                paths = [paths]

            if not paths:
                raise RUValueError(
                    fast_format_str(
                        _("Subpackage reference ${{name}} has no path."),
                        fmt={"name": name},
                    ),
                )
            spr = SubpackageReference(
                name=name,
                branch=branch,
                url=url,
                paths=[self.path / Path(p) for p in paths],
            )
            subpkgs.append(spr)

        self.subpackage_refs = subpkgs

    def _load_subpackages(self) -> None:
        self.subpackages = []
        for subpkg in self.subpackage_refs:
            if subpkg.exists():
                self.subpackages.append(Package(subpkg.get_path()))
            else:
                self.subpackages.append(None)

    def fetch(
        self,
        protocol: str,
        *,
        shallow: bool = True,
        use_direct: bool = False,
    ) -> list["Package | None"]:
        """Fetch the package.

        Args:
            protocol (str): The protocol to use.
            shallow (bool, optional): Whether to use shallow clone. Defaults to
                True.
            use_direct (bool, optional): Whether to use direct url without
                mirror speed test. Defaults to False.

        Returns:
            list[Package | None]: The fetched packages.

        """
        refs = self.subpackage_refs
        for subpkg in refs:
            subpkg.fetch(
                protocol=protocol,
                shallow=shallow,
                use_direct=use_direct,
            )

        subpkgs = [
            subpkg.fetch_subpackages(
                protocol,
                shallow=shallow,
                use_direct=use_direct,
            )
            for subpkg in refs
        ]
        self.subpackages = subpkgs
        return subpkgs
