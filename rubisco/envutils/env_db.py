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

"""Exetension env database."""

import re
import sqlite3
from pathlib import Path
from types import EllipsisType, TracebackType
from typing import Any, NoReturn

from rubisco.envutils.env_type import EnvType
from rubisco.envutils.packages import ExtensionPackageInfo
from rubisco.lib.exceptions import RUError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.sqlite_strerror import sqlite_strerror
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.version import Version

__all__ = ["RUEnvDB"]


def _regexp(pattern: str, item: str) -> bool:  # REGEX support for SQLite3.
    # Why is this not a built-in function?
    return re.fullmatch(pattern, item) is not None


_ADD_PACKAGE_SQL = """
INSERT INTO
    extensions (
        name,
        version,
        description,
        homepage,
        maintainers,
        license,
        tags,
        requirements
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)
"""


def _execute_sql(
    db: sqlite3.Connection,
    sql: str,
    args: tuple[Any, ...] | EllipsisType = ...,  # type: ignore[annotation-type-mismatch]
) -> sqlite3.Cursor:
    logger.info(
        'Executing SQL query in database "%s" with args: %s',
        str(db),
        args if args else "...",
    )
    logger.info("%s", sql)
    if args == ...:  # Avoid type warnings.
        return db.execute(sql)
    return db.execute(sql, args)


class RUEnvDB:
    """Database for extension environment."""

    db: sqlite3.Connection | None
    __path: Path
    env_type: EnvType

    def __init__(self, path: Path, env_type: EnvType) -> None:
        """Initialize the database.

        Args:
            path (Path): The path to the database.
            env_type (EnvType): The environment type.

        """
        self.__path = path
        self.db = None
        self.env_type = env_type

    def __enter__(self) -> "RUEnvDB":
        """Enter the context manager.

        Returns:
            RUEnvDB: The database.

        """
        if self.db is None:
            try:
                logger.info(
                    "Opening database '%s' for environment type '%s'.",
                    self.__path,
                    self.env_type,
                )
                self.db = sqlite3.connect(self.__path)
                self.db.create_function("REGEXP", 2, _regexp)
            except sqlite3.OperationalError as exc:
                self._rethrow_sqlite_error(exc)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the context manager.

        Args:
            exc_type (type): The exception type.
            exc_value (Exception): The exception value.
            traceback (traceback): The traceback.

        """
        if self.db is None:
            return
        self.db.close()
        self.db = None

    def __del__(self) -> None:
        """Delete the database."""
        if self.db is not None:
            self.db.close()

    def _sqlite_errmsg(self, exc: sqlite3.Error) -> str:
        return fast_format_str(
            _("[SQLite3 Errorcode ${{codename}}(${{code}})]: ${{msg}}"),
            fmt={
                "codename": exc.sqlite_errorname,
                "code": str(exc.sqlite_errorcode),
                "msg": sqlite_strerror(exc.sqlite_errorcode),
            },
        )

    def _rethrow_sqlite_error(self, exc: sqlite3.Error) -> NoReturn:
        logger.debug("Rethrowing SQLite3 error %s.", exc)
        raise RUError(
            fast_format_str(
                _(
                    "Failed to open or operate on database ${{path}}: ${{exc}}",
                ),
                fmt={
                    "path": str(self.__path),
                    "exc": self._sqlite_errmsg(exc),
                },
            ),
        ) from exc

    def add_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Add a package to the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self:
            try:
                for package in packages:
                    _execute_sql(
                        self.db,  # type: ignore[union-attr]
                        _ADD_PACKAGE_SQL,
                        (
                            package.name,
                            str(package.version),
                            package.description,
                            package.homepage,
                            ",".join(package.maintainers),
                            package.pkg_license,
                            ",".join(package.tags),
                            package.requirements,
                        ),
                    )
                    self.db.commit()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def remove_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Remove a packages from the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self:
            try:
                for package in packages:
                    _execute_sql(
                        self.db,  # type: ignore[union-attr]
                        "DELETE FROM extensions WHERE name = ?",
                        (package.name,),
                    )
                    self.db.commit()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def rollback(self) -> None:
        """Rollback the database."""
        with self:
            try:
                logger.info("Rolling back database ...")
                self.db.rollback()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def get_package(self, name: str) -> ExtensionPackageInfo:
        """Get a package from the database.

        Args:
            name (str): The package name.

        Returns:
            ExtensionPackageInfo: The package info.

        """
        with self:
            try:
                cursor = _execute_sql(
                    self.db,  # type: ignore[union-attr]
                    "SELECT * FROM extensions WHERE name = ?",
                    (name,),
                )
                row = cursor.fetchone()

                return ExtensionPackageInfo(
                    name=str(row[0]),
                    version=Version(row[1]),
                    description=str(row[2]),
                    homepage=str(row[3]),
                    maintainers=str(row[4]).split(","),
                    pkg_license=str(row[5]),
                    tags=str(row[6]).split(","),
                    requirements=str(row[7]),
                    env_type=self.env_type,
                )
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def get_all_packages(self) -> set[ExtensionPackageInfo]:
        """Get all packages from the database.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self:
            try:
                cursor = _execute_sql(
                    self.db,  # type: ignore[union-attr]
                    "SELECT * FROM extensions",
                )

                return {
                    ExtensionPackageInfo(
                        name=str(row[0]),
                        version=Version(row[1]),
                        description=str(row[2]),
                        homepage=str(row[3]),
                        maintainers=str(row[4]).split(","),
                        pkg_license=str(row[5]),
                        tags=str(row[6]).split(","),
                        requirements=str(row[7]),
                        env_type=self.env_type,
                    )
                    for row in cursor.fetchall()
                }
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def _assert_valid_regex(self, pattern: str) -> None:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise RUValueError(
                fast_format_str(
                    _("Invalid regex pattern: '${{pattern}}'."),
                    fmt={"pattern": pattern},
                ),
            ) from exc

    def _query_pkgs_with_one_pattern(
        self,
        pattern: str,
    ) -> set[ExtensionPackageInfo]:
        if pattern in ["*", ".*"]:
            return self.get_all_packages()
        # Check if the pattern is valid.
        self._assert_valid_regex(pattern)
        cursor = _execute_sql(
            self.db,  # type: ignore[union-attr]
            "SELECT * FROM extensions WHERE name REGEXP ?",
            (pattern,),
        )

        return {
            ExtensionPackageInfo(
                name=row[0],
                version=Version(row[1]),
                description=row[2],
                homepage=row[3],
                maintainers=row[4].split(","),
                pkg_license=row[5],
                tags=row[6].split(","),
                requirements=row[7],
                env_type=self.env_type,
            )
            for row in cursor.fetchall()
        }

    def query_packages(self, patterns: list[str]) -> set[ExtensionPackageInfo]:
        """Query packages from the database.

        Args:
            patterns (str): The regex patterns.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self:
            res: set[ExtensionPackageInfo] = set()
            try:
                for pattern in patterns:
                    res |= self._query_pkgs_with_one_pattern(pattern)
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)
            return res
