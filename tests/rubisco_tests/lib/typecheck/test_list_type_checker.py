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

"""Test rubisco.lib.typecheck.list_type_check module."""

import pytest

from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.typecheck import get_list_check


def test_list_type_checking() -> None:
    """Test list type checking."""
    lst: list[int] = [1, 2, 3]

    if get_list_check(lst, 0, int) != 1:
        pytest.fail("TypeCheckingList get method failed.")

    with pytest.raises(RUTypeError):
        get_list_check(lst, 1, str)

    with pytest.raises(IndexError):
        get_list_check(lst, 10, int)
