# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
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

"""Test rubisco.lib.archive module."""

from pathlib import Path

import pytest

from rubisco.lib.archive import compress, extract
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import TemporaryObject


class TestArchive:
    """Test archive module."""

    def _check_extract_archive(self, path: Path) -> None:
        """Check extract archive.

        Args:
            path (Path): Extract destination.

        """
        if not path.is_dir():
            pytest.fail("Extract destination not a directory.")
        if not (path / "dir1").is_dir():
            pytest.fail("dir1 not exists.")
        if not (path / "dir1" / "file1").is_file():
            pytest.fail("file1 not exists.")
        if (path / "dir1" / "file1").stat().st_size != 0:
            pytest.fail("file1 not empty.")
        with (path / "file2").open(encoding="utf-8") as f:
            if f.read() != "Test\n":
                pytest.fail("file2 content not correct.")
        if not (path / "file3").is_file():
            pytest.fail("file3 not exists.")

    def _extract(self, compress_type: str, password: str = "") -> None:
        with TemporaryObject.new_directory(suffix="test") as path:
            archive_file = Path(f"tests/test.{compress_type}")
            if password:
                archive_file = Path(f"tests/test-pwd.{compress_type}")
            extract(
                archive_file,
                path.path / "test",
                password=password,
                allow_absolute_dest=True,
            )
            self._check_extract_archive(path.path / "test")

    def test_extract_zip(self) -> None:
        """Test extract zip."""
        self._extract("zip")

    def test_extract_tar_gz(self) -> None:
        """Test extract tar.gz."""
        self._extract("tar.gz")

    def test_extract_tar_xz(self) -> None:
        """Test extract tar.xz."""
        self._extract("tar.xz")

    def test_extract_tgz(self) -> None:
        """Test extract tgz (alias of tar.gz)."""
        self._extract("tgz")

    def test_extract_password_zip(self) -> None:
        """Test extract zip with password."""
        self._extract("zip", password="1234")  # noqa: S106

    def test_extract_invalid_password(self) -> None:
        """Test extract zip with invalid password."""
        with pytest.raises(RuntimeError):
            self._extract("zip", password="0")  # noqa: S106

    def test_extract_to_absolute(self) -> None:
        """Test extract tgz (alias of tar.gz)."""
        self._extract("tgz")

    def _compress(self, compress_type: str) -> None:
        with TemporaryObject.new_directory(suffix="test") as path:
            compress(
                Path("tests/data").absolute(),
                path.path / f"test.{compress_type}",
                start=Path("tests/data").absolute(),
                compress_type=compress_type,
                compress_level=9,
                allow_absolute_dest=True,
            )
            extract(
                path.path / f"test.{compress_type}",
                path.path / "extract",
                compress_type=compress_type,
                allow_absolute_dest=True,
            )
            self._check_extract_archive(path.path / "extract")

    def test_compress_zip(self) -> None:
        """Test compress zip."""
        self._compress("zip")

    def test_compress_tar_gz(self) -> None:
        """Test compress tar.gz."""
        self._compress("tar.gz")

    def test_compress_tar_xz(self) -> None:
        """Test compress tar.xz."""
        self._compress("tar.xz")

    def test_compress_tgz(self) -> None:
        """Test compress tgz (alias of tar.gz)."""
        self._compress("tgz")

    def test_compress_to_absolute(self) -> None:
        """Test compress to absolute path."""
        with (
            TemporaryObject.new_directory(suffix="test") as path,
            pytest.raises(RUValueError),
        ):
            compress(
                Path("tests/data").absolute(),
                (path.path / "test.zip").absolute(),
                start=Path("tests/data"),
                compress_level=9,
                allow_absolute_dest=False,
            )

    def test_compress_invalid_type(self) -> None:
        """Test compress invalid type."""
        with (
            TemporaryObject.new_directory(suffix="test") as path,
            pytest.raises(RUValueError),
        ):
            compress(
                Path("tests/data").absolute(),
                path.path / "test.zip",
                start=Path("tests/data"),
                compress_type="invalid",
                compress_level=9,
                allow_absolute_dest=True,
            )
