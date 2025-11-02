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

"""Rubisco dependency generators."""

from abc import ABC, abstractmethod

from rubisco.shared.api.kernel import RUConfiguration

__all__ = [
    "IDependencyGenerator",
    "generate_dependencies",
    "register_generator",
]


class IDependencyGenerator(ABC):
    """Dependency generator."""

    @abstractmethod
    def __init__(self, config: RUConfiguration) -> None:
        """Initialize the dependency generator.

        Args:
            config (RUConfiguration): Project config file.

        """

    @abstractmethod
    def need_generate(self) -> bool:
        """Check if we need to generate dependencies by this generator.

        Returns:
            bool: True if we need to generate dependencies by this generator,
                False otherwise.

        """

    @abstractmethod
    def generate(self) -> list[dict[str, str]]:
        """Generate the dependency file.

        Returns:
            list[dict[str, str]]: Dependency content.

        """


generators: list[type[IDependencyGenerator]] = []


def register_generator(generator: type[IDependencyGenerator]) -> None:
    """Register generator.

    Args:
        generator (type[IDependencyGenerator]): The generator type.

    """
    generators.append(generator)


def generate_dependencies(config: RUConfiguration) -> list[dict[str, str]]:
    """Generate dependencies.

    Args:
        config (RUConfiguration): Configuration.

    Returns:
        list[dict[str, str]]: Dependencies metadata.

    """
    res: list[dict[str, str]] = []
    for generator_type in generators:
        generator = generator_type(config)
        if generator.need_generate():
            res.extend(generator.generate())

    return res
