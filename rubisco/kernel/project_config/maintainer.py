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

"""Maintainer class definition.

The maintainer text's format is "Name <Email> (Homepage)". The email and
homepage is optional.
"""

import re
from dataclasses import dataclass

from beartype import beartype

from rubisco.lib.log import logger
from rubisco.lib.typecheck import get_dict_check

_PATTERN = re.compile(r"^([^<(]+?)(?:\s*<([^>]+)>)?(?:\s*\(([^)]+)\))?$")


@dataclass(frozen=True)
class Maintainer:
    """Maintainer class."""

    name: str
    email: str | None
    homepage: str | None

    @classmethod
    @beartype
    def parse(
        cls,
        text: str | dict[str, str | None],
    ) -> "Maintainer":
        """Parse maintainer text.

        Args:
            text (str | dict[str, str | None]): The maintainer text or dict.

        Returns:
            Maintainer: Maintainer object.

        """
        if isinstance(text, str):
            match = re.match(_PATTERN, text)
            if match:
                name, email, homepage = match.groups()
                name = str(name)
                email = str(email) if email else None
                homepage = str(homepage) if homepage else None
            else:
                logger.warning("Failed to match maintainer: %s", text)
                name = text
                email = None
                homepage = None
        else:
            name = str(get_dict_check(text, "name", valtype=str))
            email = str(
                get_dict_check(
                    text,
                    "email",
                    default=None,
                    valtype=str | None,
                ),
            )
            homepage = str(
                get_dict_check(
                    text,
                    "homepage",
                    default=None,
                    valtype=str | None,
                ),
            )
        return Maintainer(name=name, email=email, homepage=homepage)

    def to_dict(self) -> dict[str, object]:
        """Convert maintainer to dict.

        Returns:
            dict[str, object]: The result dict.

        """
        return {
            "name": self.name,
            "email": self.email,
            "homepage": self.homepage,
        }

    def __str__(self) -> str:
        """Convert maintainer to string.

        Returns:
            str: The result string.

        """
        res = self.name
        if self.email:
            res += f" <[link=mailto:{self.email}][white]{self.email}[/][/link]>"
        if self.homepage:
            res += f" ([blue][underline]{self.homepage}[/underline][/blue] )"

        return res
