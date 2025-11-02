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

"""Rubisco config file loader."""

import tomllib
from pathlib import Path
from typing import Any, TextIO

import json5 as json
import yaml
from beartype import beartype

from rubisco.config import DEFAULT_CHARSET
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import type_assert
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.format import format_auto
from rubisco.lib.variable.utils import make_pretty, merge_dict

__all__ = ["SUPPORTED_EXTS", "RUConfiguration"]


def _toml_loadfunc(f: TextIO) -> dict[str, Any]:
    return tomllib.loads(f.read())


SUPPORTED_EXTS = {".json", ".json5", ".cfg", ".toml", ".ini", ".yml", ".yaml"}


class RUConfiguration:
    """Rubisco configuration."""

    path: Path
    config: dict[str, object]

    def __init__(
        self,
        path: Path | None = None,
        init: dict[str, object] | None = None,
    ) -> None:
        """Initialize configuration.

        Args:
            path (Path | None): Config file path.
            init (dict[str, object] | None): Initial data.

        """
        self.config = init or {}
        self.path = path or Path()

    @classmethod
    def __load_from_file(
        cls,
        path: Path,
        loaded: list[Path],
    ) -> dict[str, object]:
        with path.open(encoding=DEFAULT_CHARSET) as f:
            if path.suffix in {".json", ".json5"}:
                loadfunc = json.load
                filetype = "JSON5"
            elif path.suffix in {".cfg", ".toml", ".ini"}:
                loadfunc = _toml_loadfunc
                filetype = "TOML"
            elif path.suffix in {".yml", ".yaml"}:
                loadfunc = yaml.safe_load
                filetype = "YAML"
            else:
                raise RUValueError(
                    fast_format_str(
                        _("Unknown file type: ${{path}}"),
                        fmt={
                            "path": make_pretty(path),
                        },
                    ),
                )

            logger.debug("Loading config file as '%s': %s", filetype, path)
            mapping = type_assert(loadfunc(f), dict[str, object])
            includes: list[str] = format_auto(
                mapping.get("includes", []),
                valtype=list[str],
            )
            loaded.append(path)
            for file in includes:
                fp = path.parent / file
                merge_dict(mapping, cls.__load_from_file(fp, loaded))

        return mapping

    @classmethod
    def _load_from_file(
        cls,
        path: Path,
        loaded: list[Path],
    ) -> dict[str, object]:
        path = path.resolve()
        if path in loaded:
            logger.warning("Circular dependency detected: %s", path)
            return {}
        mapping = cls.__load_from_file(path, loaded)

        dirpath = Path(str(path) + ".d")
        if dirpath.is_dir():
            for file in dirpath.rglob("*"):
                if file.is_file():
                    merge_dict(mapping, cls.__load_from_file(file, loaded))

        return mapping

    @beartype
    @classmethod
    def load_from_file(cls, path: Path) -> "RUConfiguration":
        """Load configuration from file.

        Args:
            path (Path): File path.

        Returns:
            RUConfiguration: The configuration.

        """
        if not path.is_file():
            for ext in SUPPORTED_EXTS:
                p = path.with_suffix(ext)
                if p.is_file():
                    return cls(p, cls._load_from_file(p, []))
        return cls(path, cls._load_from_file(path, []))

    @beartype
    def merge(self, other: "dict[str, object] | RUConfiguration") -> None:
        """Merge other configuration to this configuration.

        Args:
            other (dict[str, object] | RUConfiguration): The other
                configuration mapping or RUConfiguration object.

        """
        if isinstance(other, RUConfiguration):
            merge_dict(self.config, other.config)
        else:
            merge_dict(self.config, other)
