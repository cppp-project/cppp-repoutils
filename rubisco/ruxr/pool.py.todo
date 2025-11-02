# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2025 The C++ Plus Project.
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

"""Fetching package pool infomation."""

from dataclasses import dataclass

from beartype import beartype
from dacite import Config, from_dict

from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.lib.version import Version


@dataclass
class PackageItem:
    """Package item information in pool."""

    name: str
    description: str
    version: Version

    @classmethod
    @beartype
    def from_dict(cls, data: dict[str, str]) -> "PackageItem":
        """Create a PackageItem instance from a dict.

        Args:
            data: The dict data.

        Returns:
            A Package instance.

        """
        return from_dict(cls, data, config=Config(cast=[Version]))


@dataclass
class Pool:
    """Package pool information."""

    pool: list[PackageItem]

    @classmethod
    @beartype
    def from_dict(cls, data: dict[str, list[dict[str, str]]]) -> "Pool":
        """Create a Pool instance from a dict.

        Args:
            data: The dict data.

        Returns:
            A Pool instance.

        """
        pool = [PackageItem.from_dict(package) for package in data["pool"]]
        return cls(pool)


@dataclass
class Package:
    """Package detailed information."""

    name: str
    description: str
    versions: list[dict[str, str | Version]]
    icon: str  # URL
    license: str  # License name
    maintainers: list[Maintainer]
    homepage: str  # URL
    deps: list[str | dict[str, str]]

    @staticmethod
    def _field_name_transformer(field_name: str) -> str:
        return field_name.replace("_", "-")

    @classmethod
    @beartype
    def from_dict(
        cls,
        data: dict[str, str | list[dict[str, str]]],
    ) -> "Package":
        """Create a Package instance from a dict.

        Args:
            data: The dict data.

        Returns:
            A Package instance.

        """
        return from_dict(
            cls,
            data,
            config=Config(
                cast=[Version],
                type_hooks={Maintainer: Maintainer.parse},
                field_name_transformer=cls._field_name_transformer,
            ),
        )
