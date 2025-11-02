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

"""Test for rubisco.lib.variable.utils."""

import pytest

from rubisco.lib.variable.utils import iter_assert, merge_dict


class TestUtils:
    """Test class for rubisco.lib.variable.utils."""

    def test_iter_assert(self) -> None:
        """Test iter_assert function."""
        iter_assert([1, 2, 3], lambda _: True, ValueError)
        iter_assert([1, 2, 3], lambda x: x > 0, ValueError)
        with pytest.raises(RuntimeError):
            iter_assert([1, 2, -3], lambda x: x > 0, RuntimeError)

    def test_merge_dict(self) -> None:
        """Test merge_dict function."""
        dst: dict[object, object] = {
            "a": 1,
            "b": {
                "x": 0,
                "c": 2,
                "d": 3,
            },
            "e": True,
            "l": [1, 2, 3],
            "n": None,
            "m": [1],
        }
        src: dict[object, object] = {
            "A": "alpha",  # New key.
            "b": {
                "C": "gamma",  # New nested key.
                "d": 4,  # Overwrite existing value.
                "c": [3, 5, 0, 2, 3, 4],  # Overwrite to list.
            },
            "E": False,  # New key.
            "l": [4, 5, 6],  # Overwrite existing value.
            "m": 1.0,  # Overwrite list.
        }
        merge_dict(dst, src)
        if dst != {
            "A": "alpha",  # New key.
            "a": 1,
            "b": {
                "C": "gamma",  # New nested key.
                "x": 0,
                "c": [3, 5, 0, 2, 3, 4],  # Overwrite to list.
                "d": 4,  # Overwrite existing value.
            },
            "E": False,  # New key.
            "e": True,
            "l": [1, 2, 3, 4, 5, 6],  # Overwritten to list.
            "n": None,
            "m": 1.0,  # Overwrite list.
        }:
            pytest.fail(
                f"dst is not merged correctly. Expected: {dst}\nGot: {src}",
            )
