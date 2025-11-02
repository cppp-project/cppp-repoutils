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

"""Test rubisco.lib.typecheck.dict_type_check module."""

import pytest

from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.typecheck import get_dict_check


def test_dict_type_checking() -> None:
    """Test dict type checking."""
    dct: dict[str, int | dict[str, list[int | None]]] = {
        "a": 1,
        "b": 2,
        "c": {"d": [1, 2, 3, None]},
    }

    if get_dict_check(dct, "a", int) != 1:
        pytest.fail("Check failed.")

    with pytest.raises(RUTypeError):
        get_dict_check(dct, "b", str)

    with pytest.raises(RUTypeError):
        get_dict_check(dct, "c", dict[str, list[str]])

    if get_dict_check(dct, "c", dict[str, list[int | None]]) != {
        "d": [1, 2, 3, None],
    }:
        pytest.fail("Nested dict check failed.")

    with pytest.raises(RUTypeError):
        get_dict_check(dct, "c", dict[str, list[int | str]])
