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

"""Convert a string literal to specific type."""

from __future__ import annotations

import math
from typing import cast

import json5

from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str


def _size_to_int(  # noqa: PLR0911 PLR0912 C901 # pylint: disable=R0911, R0912
    value: str,
) -> int:
    value = value.lower()
    if value.endswith("k"):
        return int(value[:-1]) * 1024
    if value.endswith("m"):
        return int(value[:-1]) * 1024 * 1024
    if value.endswith("g"):
        return int(value[:-1]) * 1024 * 1024 * 1024
    if value.endswith("t"):
        return int(value[:-1]) * 1024 * 1024 * 1024 * 1024
    if value.endswith("p"):
        return int(value[:-1]) * 1024 * 1024 * 1024 * 1024 * 1024
    if value.endswith("kb"):
        return int(value[:-2]) * 1024
    if value.endswith("mb"):
        return int(value[:-2]) * 1024 * 1024
    if value.endswith("gb"):
        return int(value[:-2]) * 1024 * 1024 * 1024
    if value.endswith("tb"):
        return int(value[:-2]) * 1024 * 1024 * 1024 * 1024
    if value.endswith("pb"):
        return int(value[:-2]) * 1024 * 1024 * 1024 * 1024 * 1024
    if value.endswith("kib"):
        return int(value[:-3]) * 1024
    if value.endswith("mib"):
        return int(value[:-3]) * 1024 * 1024
    if value.endswith("gib"):
        return int(value[:-3]) * 1024 * 1024 * 1024
    if value.endswith("tib"):
        return int(value[:-3]) * 1024 * 1024 * 1024 * 1024
    if value.endswith("pib"):
        return int(value[:-3]) * 1024 * 1024 * 1024 * 1024 * 1024
    if value.endswith("ki"):
        return int(value[:-2]) * 1024
    if value.endswith("mi"):
        return int(value[:-2]) * 1024 * 1024
    if value.endswith("gi"):
        return int(value[:-2]) * 1024 * 1024 * 1024
    if value.endswith("ti"):
        return int(value[:-2]) * 1024 * 1024 * 1024 * 1024
    if value.endswith("pi"):
        return int(value[:-2]) * 1024 * 1024 * 1024 * 1024 * 1024
    if value.endswith("b"):
        return int(value[:-1])
    return int(value, base=0)


def convert_to[T](  # noqa: PLR0911 C901  # pylint: disable=R0911
    value: str | T,
    as_type: type[T],
) -> T:
    """Convert a string literal to specific type.

    Args:
        value (str | T): The string literal or the value.
        as_type (type[T]): The type to convert to.

    Returns:
        T: The converted value.

    Raises:
        RUValueError: If we cannot convert the value to the specified type.

    """
    if isinstance(value, as_type):
        return value

    value_ = cast("str", value)

    if as_type is bool:
        if value_.lower() in {"false", "no", "off", "n", "0"}:
            return cast("T", val=False)
        return cast("T", val=True)
    if as_type is int:
        return cast("T", _size_to_int(value_))
    if as_type is float:
        # This is totally useless, just for fun.
        if value_.lower() in {"pi", "\u03c0"}:
            return cast("T", math.pi)
        if value_.lower() == "e":
            return cast("T", math.e)
        return cast("T", float(value_))
    if as_type is str:
        return cast("T", value_)
    if as_type is list:
        return cast("T", value_.split(","))
    if as_type is tuple:
        return cast("T", tuple(value_.split(",")))
    if as_type is set:
        return cast("T", set(value_.split(",")))
    if as_type is dict:
        return cast("T", json5.loads(value_))
    raise RUTypeError(
        fast_format_str(
            _("Cannot convert value ${{value}} to type ${{type}}"),
            fmt={"value": repr(value), "type": as_type.__name__},
        ),
    )
