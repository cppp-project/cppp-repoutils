# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-rubisco.
#
# cppp-Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""File utilities."""

from __future__ import annotations

import atexit
import fnmatch
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Self

from rubisco.config import APP_NAME
from rubisco.lib.exceptions import (
    RUOSError,
    RUShellExecutionError,
    RUValueError,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FunctionType, TracebackType

__all__ = [
    "TemporaryObject",
    "check_file_exists",
    "copy_recursive",
    "find_command",
    "glob_path",
    "human_readable_size",
    "resolve_path",
    "rm_recursive",
]


def check_file_exists(path: Path) -> None:
    """Check if the file exists. If exists, ask UCI to overwrite it.

    Args:
        path (Path): The path to check.

    Raises:
        AssertionError: If the file or directory exists and user choose to
            skip.

    """
    if path.exists():
        call_ktrigger(IKernelTrigger.file_exists, path=path)
        # UCI will raise an exception if user choose to skip.
        rm_recursive(path, strict=True)


def assert_rel_path(path: Path) -> None:
    """Assert that the path is a relative path.

    Args:
        path (Path): The path to assert.

    Raises:
        RUValueError: If the path is not a relative path.

    """
    if path.is_absolute():
        raise RUValueError(
            fast_format_str(
                _(
                    "Absolute path ${{path}} is not allowed.",
                ),
                fmt={"path": make_pretty(path)},
            ),
        )


def rm_recursive(
    path: Path,
    *,
    strict: bool = True,
) -> None:
    """Remove a file or directory recursively.

    Args:
        path (Path): The path to remove.
        strict (bool): Raise an exception if error occurs.

    Raises:
        OSError: If strict is True and an error occurs.

    """
    path = path.absolute()
    if path == Path("/").absolute():
        raise RUValueError(
            fast_format_str(
                _("Cannot remove root directory."),
            ),
        )

    def _onexc(  # pylint: disable=unused-argument
        func: FunctionType | None,  # noqa: ARG001
        path: str | Path,
        exc: BaseException,
    ) -> None:
        if not strict:
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _(
                        "Error while removing ${{path}}: ${{error}}",
                    ),
                    fmt={"path": make_pretty(path), "error": str(exc)},
                ),
            )

    def _onerror(
        func: FunctionType,
        path: str | Path,
        exc_info: tuple[type, BaseException, TracebackType],
    ) -> None:
        return _onexc(func, path, exc_info[1])

    try:
        if path.is_dir() and not path.is_symlink():
            if sys.version_info < (3, 13):
                shutil.rmtree(  # pylint: disable=deprecated-argument
                    path,
                    ignore_errors=not strict,
                    onerror=_onerror,  # type: ignore[arg-type]
                )
            else:
                shutil.rmtree(  # pylint: disable=unexpected-keyword-arg
                    path,
                    ignore_errors=not strict,
                    onexc=_onexc,  # type: ignore[arg-type]
                )
        else:
            path.unlink()
        logger.debug("Removed '%s'.", str(path))
    except OSError as exc:
        if strict:
            raise RUOSError(exc) from exc
        _onexc(None, path, exc)
        logger.warning("Failed to remove '%s'.", str(path), exc_info=exc)


def _match_path_only(pattern: str) -> bool:
    return "/" in pattern


def _ignore_patterns(
    patterns: list[str],
    start_dir: Path,
) -> Callable[[str, list[str]], set[str]]:
    """Return the function that can be used as `copytree()` ignore parameter.

    Patterns is a sequence of glob-style patterns
    that are used to exclude files

    """
    patterns = [pattern for pattern in patterns if pattern]

    def __ignore_patterns(strpath: str, strnames: list[str]) -> set[str]:
        path = Path(strpath).relative_to(start_dir)  # Always noexcept.
        names = [(path / Path(name)).as_posix() for name in strnames]
        ignored_names: list[str] = []

        for pattern in patterns:
            if _match_path_only(pattern):
                res = fnmatch.filter(names, pattern)
                ignored_names.extend([Path(i).name for i in res])
            else:
                ignored_names.extend(fnmatch.filter(strnames, pattern))
        return set(ignored_names)

    return __ignore_patterns


def copy_recursive(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dst: Path,
    ignore: list[str] | None = None,
    *,
    strict: bool = False,
    symlinks: bool = False,
    exists_ok: bool = False,
) -> None:
    """Copy a file or directory recursively.

    Args:
        src (Path): The source path to copy.
        dst (Path): The destination path.
        strict (bool): Raise an exception if error occurs.
        ignore (list[str] | None): The list of files to ignore.
        symlinks (bool): Copy symlinks as symlinks.
        exists_ok (bool): Do not raise an exception if the destination exists.

    Raises:
        OSError: If strict is True and an error occurs.

    """
    if ignore is None:
        ignore = []

    src = src.absolute()
    dst = dst.absolute()
    try:
        if src.is_dir():
            shutil.copytree(
                src,
                dst,
                symlinks=symlinks,
                dirs_exist_ok=exists_ok,
                ignore=_ignore_patterns(ignore, src),
            )
        else:
            if dst.is_dir():
                dst = dst / src.name
            if dst.exists() and not exists_ok:
                raise FileExistsError(
                    fast_format_str(
                        _(
                            "File ${{path}} already exists.",
                        ),
                        fmt={"path": make_pretty(dst)},
                    ),
                )
            dst = Path(shutil.copy2(src, dst, follow_symlinks=not symlinks))
        logger.debug("Copied '%s' to '%s'.", str(src), str(dst))
    except OSError as exc:
        if strict:
            raise RUOSError(exc) from exc
        logger.warning(
            "Failed to copy '%s' to '%s'.",
            str(src),
            str(dst),
            exc_info=exc,
        )


tempdirs: set[TemporaryObject] = set()


def new_tempdir(prefix: str = "", suffix: str = "") -> Path:
    """Create temporary directory but do not register it.

    Args:
        prefix (str): The prefix of the temporary directory
        suffix (str): The suffix of the temporary directory.

    Returns:
        str: The temporary directory.

    """
    return Path(
        tempfile.mkdtemp(
            suffix=suffix,
            prefix=prefix,
            dir=tempfile.gettempdir(),
        ),
    ).absolute()


def new_tempfile(prefix: str = "", suffix: str = "") -> tuple[Path, int]:
    """Create temporary file but do not register it.

    Args:
        prefix (str): The prefix of the temporary file.
        suffix (str): The suffix of the temporary file.

    Returns:
        The tempfile path and its fd.

    """
    fd, path = tempfile.mkstemp(
        suffix=suffix,
        prefix=prefix,
        dir=tempfile.gettempdir(),
    )
    return Path(path).absolute(), fd


class TemporaryObject:
    """A context manager for temporary files or directories."""

    # Type of the temporary object.
    TYPE_FILE: int = 0
    # Type of the temporary object.
    TYPE_DIRECTORY: int = 1
    # Auto-detecting the type of the temporary object. For register_tempobject.
    TYPE_AUTO: int = 2

    __path: Path
    __type: int
    __moved: bool = False
    __fd: int | None

    def __init__(
        self,
        temp_type: int,
        path: Path,
        *,
        fd: int | None = None,
    ) -> None:
        """Create a temporary object.

        Args:
            temp_type (int): The type of the temporary object.
                Can be TemporaryObject.TYPE_FILE or
                TemporaryObject.TYPE_DIRECTORY.
            path (Path): The path of the temporary object.
                We will register it for temporary later.
            fd (int): The file descriptor of the tempfile.
                Default to None.

        """
        self.__type = temp_type
        self.__path = path
        self.__fd = fd
        tempdirs.add(self)
        logger.debug("Registered temporary object '%s'.", str(self.__path))

    def __enter__(self) -> Self:
        """Enter the context manager.

        Returns:
            TemporaryObject: The temporary object path.

        """
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
        self.remove()

    def __str__(self) -> str:
        """Get the string representation of the temporary object.

        Returns:
            str: The string representation of the temporary object.

        """
        return str(self.path)

    def __repr__(self) -> str:
        """Get the string representation of the temporary object.

        Returns:
            str: The string representation of the temporary object.

        """
        return f"TemporaryDirectory({self.path!r})"

    def __hash__(self) -> int:
        """Get the hash of the temporary object.

        Returns:
            int: The hash of the temporary object.

        """
        return hash(self.path)

    def __eq__(self, obj: object) -> bool:
        """Compare the temporary object with another object.

        Args:
            obj (object): The object to compare.

        Returns:
            bool: True if the temporary object is equal to the object,
                False otherwise.

        """
        if not isinstance(obj, TemporaryObject):
            return False
        return self.path == obj.path

    def __ne__(self, obj: object) -> bool:
        """Compare the temporary object with another object.

        Args:
            obj (object): The object to compare.

        Returns:
            bool: True if the temporary object is not equal to the object,
                False otherwise.

        """
        return not self == obj

    @property
    def path(self) -> Path:
        """Get the temporary object path.

        Returns:
            Path: The temporary object path.

        """
        return self.__path

    @property
    def temp_type(self) -> int:
        """Get the temporary object type.

        Returns:
            int: The temporary object type.

        """
        return self.__type

    def is_file(self) -> bool:
        """Check if the temporary object is a file.

        Returns:
            bool: True if the temporary object is a file, False otherwise.

        """
        return self.path.is_file()

    def is_dir(self) -> bool:
        """Check if the temporary object is a object.

        Returns:
            bool: True if the temporary object is a object, False otherwise.

        """
        return self.path.is_dir()

    def remove(self) -> None:
        """Remove the temporary object."""
        if self.__moved:
            return
        if self.__fd:
            os.close(self.__fd)
        if self.path.is_file():
            self.path.unlink()
        else:
            shutil.rmtree(self.path, ignore_errors=False)
        self.move()

    def move(self) -> Path:
        """Release the ownership of this temporary object.

        Returns:
            Path: The new location of the temporary object.

        """
        if self.__moved:
            return self.path
        try:
            tempdirs.remove(self)
            logger.debug("Unregistered temporary object '%s'.", str(self.path))
        except KeyError as exc:
            logger.warning(
                "Temporary object '%s' not found when unregistering.",
                str(self.path),
                exc_info=exc,
            )
        self.__moved = True
        return self.path

    @classmethod
    def new_file(cls, prefix: str = APP_NAME, suffix: str = "") -> Self:
        """Create a temporary file.

        Args:
            prefix (str, optional): Prefix of the temporary path.
                Defaults to APP_NAME.
            suffix (str, optional): Suffix of the temporary path.
                Defaults to "".

        Returns:
            TemporaryObject: The temporary file.

        """
        path, fd = new_tempfile(prefix=prefix, suffix=suffix)
        return cls(cls.TYPE_FILE, path, fd=fd)

    @classmethod
    def new_directory(cls, prefix: str = APP_NAME, suffix: str = "") -> Self:
        """Create a temporary directory.

        Args:
            prefix (str, optional): Prefix of the temporary path.
                Defaults to APP_NAME.
            suffix (str, optional): Suffix of the temporary path.
                Defaults to "".

        Returns:
            TemporaryObject: The temporary directory.

        """
        return cls(
            cls.TYPE_DIRECTORY,
            new_tempdir(prefix=prefix, suffix=suffix),
        )

    @classmethod
    def register_tempobject(
        cls,
        path: Path,
        path_type: int = TYPE_AUTO,
    ) -> Self:
        """Register a file or a directory to a temporary object.

        Args:
            path (Path): The path of the object.
            path_type (int, optional): The type of the object.
                Can be TYPE_FILE, TYPE_DIRECTORY or TYPE_AUTO.
                If TYPE_FILE or TYPE_DIRECTORY is specified, create a temporary
                object with the specified type. If TYPE_AUTO is specified,
                auto-detect the type of the object. Defaults to TYPE_AUTO.

        Returns:
            TemporaryObject: Registered temporary object.

        """
        match path_type:
            case cls.TYPE_AUTO:
                return cls(
                    cls.TYPE_DIRECTORY if path.is_dir() else cls.TYPE_FILE,
                    path,
                )
            case cls.TYPE_FILE:
                if not path.exists():
                    path.touch()
                elif not path.is_file():
                    msg = fast_format_str(
                        _("Invalid type: ${{path}}, expected file."),
                        fmt={"path": make_pretty(path)},
                    )
                    raise RUValueError(msg)
                return cls(cls.TYPE_FILE, path)
            case cls.TYPE_DIRECTORY:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                elif not path.is_dir():
                    msg = fast_format_str(
                        _("Invalid type: ${{path}}, expected directory."),
                        fmt={"path": make_pretty(path)},
                    )
                    raise RUValueError(msg)
                return cls(cls.TYPE_DIRECTORY, path)
            case _:
                msg = "Invalid path type."
                raise ValueError(msg)

    @classmethod
    def cleanup(cls) -> None:
        """Clean up all temporary directories."""
        for tempdir in tempdirs.copy():
            tempdir.remove()
        tempdirs.clear()


def resolve_path(
    path: Path,
    *,
    absolute_only: bool = True,
) -> Path:
    """Resolve a path with globbing support.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool): Absolute path only instead of resolve.
            Defaults to True.

    Returns:
        Path: Resolved path.

    """
    res = path.expanduser().absolute()
    if absolute_only:
        return res
    return res.resolve()


def glob_path(
    path: Path,
    *,
    absolute_only: bool = True,
) -> list[Path]:
    """Resolve a path and globbing it.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool, optional): Absolute path only instead of resolve.
            Defaults to False.

    Returns:
        list[Path]: List of resolved paths.

    """
    path = resolve_path(path, absolute_only=absolute_only)
    if not path.is_dir():
        return [path]
    return list(path.glob("*"))


def human_readable_size(size: float) -> str:
    """Convert size to human readable format.

    Args:
        size (float): The size to convert.

    Returns:
        str: The human readable size.

    """
    unit = "B"
    for unit_ in ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"):
        unit = unit_
        if size < 1024.0:  # noqa: PLR2004
            break
        size /= 1024.0
    return f"{size:.2f}{unit}"


def find_command(
    cmd: str,
    *,
    strict: bool = True,
) -> str | None:
    """Find the command in the system.

    Args:
        cmd (str): The command to find.
        strict (bool, optional): Raise an exception if the command is not
            found. Defaults to True.

    Returns:
        str: The command path.

    """
    res = shutil.which(cmd)

    logger.info(
        "Checking for command '%s' ... %s",
        cmd,
        res or "not found.",
    )

    if strict and res is None:
        raise RUShellExecutionError(
            fast_format_str(
                _("Command '${{cmd}}' not found."),
                fmt={"cmd": cmd},
            ),
            retcode=RUShellExecutionError.RETCODE_COMMAND_NOT_FOUND,
        )

    return res or None


# Register cleanup function.
atexit.register(TemporaryObject.cleanup)
