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

"""Test for rubisco config loader."""

from pathlib import Path

import pytest

from rubisco.kernel.config_loader import RUConfiguration
from rubisco.lib.exceptions import RUExprError
from rubisco.lib.variable.format import FormatMode, format_auto
from rubisco.lib.variable.variable import push_variables, variables


class TestConfigLoader:
    """Test for rubisco config loader."""

    def _reset(self) -> None:
        """Reset the variable container."""
        variables.clear()

    def test_load(self) -> None:
        """Test for rubisco config loader."""
        self._reset()

        res: dict[str, object] = {
            "a": 2,
            "b": ["B", 1, 2, 3],
            "c": [1, 2, 3, 4],
            "d": {
                "aa": 11,
                "bb": "bb",
                "cc": [11, 22],
                "dd": {"a": 1, "xxxx": [{"a": 1}, {"b": 2}], "b": 1},
                "ee": "ef",
            },
            "includes": ["test.include.json"],
        }
        config = RUConfiguration.load_from_file(Path("tests/test.json5"))
        d = config.config
        if d != res:
            pytest.fail(f"Expect {res}, got {d}")

    def test_merge(self) -> None:
        """Test for rubisco config loader merge."""
        self._reset()

        res: dict[str, object] = {
            "a": 2,
            "b": ["B", 1, 2, 3],
            "c": [1, 2, 3, 4, 5, 6, 7, 8],
            "d": {
                "aa": 11,
                "bb": "bb",
                "cc": [11, 22],
                "dd": {"a": 1, "xxxx": [{"a": 1}, {"b": 2}], "b": 1},
                "ee": "ef",
                "X": "wsad",
            },
            "includes": ["test.include.json"],
            "MGR": 1,
            "X": 1.0,
            "A": True,
        }

        pre: dict[str, object] = {
            "A": True,
            "a": 0,
        }
        config = RUConfiguration(Path("tests/test.json5"), pre)
        config.merge(RUConfiguration.load_from_file(Path("tests/test.json5")))
        config.merge(
            RUConfiguration.load_from_file(Path("tests/test-post-merge.ini")),
        )
        config.merge({"X": 1.0})

        if config.config != res:
            pytest.fail(f"Expect {res}, got {config.config}")

    def test_format(self) -> None:
        """Test for rubisco config loader format."""
        self._reset()

        config = RUConfiguration(
            Path(),
            {
                "A": True,
                "B": "${{var}}",
                "X": {"C": "123", "d": [1, 2, "${{ undef :${{p}}}}"]},
                "expr": "$&{{ g('var').split(',') }}",
            },
        )
        with pytest.raises(RUExprError):
            format_auto(config.config.get("B"))

        push_variables("var", "C")
        res = format_auto(format_auto(config.config["X"], fmt={"p": "d"})["C"])
        if res != "123":
            pytest.fail(f"Expect 123, got {res}")

        with pytest.raises(RUExprError):
            format_auto(config.config["expr"])

        res = format_auto(
            config.config["expr"],
            mode=FormatMode.EXECUTE,
            fmt={"var": "C,D"},
        )
        if res != ["C", "D"]:
            pytest.fail(f"Expect ['C', 'D'], got {res}")
