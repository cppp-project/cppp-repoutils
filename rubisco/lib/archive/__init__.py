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

"""Archive compression/extraction utilities."""

from __future__ import annotations

import bz2
import gzip
import lzma
import os
import tarfile
import zipfile
from pathlib import Path

from rubisco.config import COPY_BUFSIZE
from rubisco.lib.archive.tar import compress_tarball, extract_tarball
from rubisco.lib.archive.zip import compress_zip, extract_zip
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import (
    assert_rel_path,
    check_file_exists,
    rm_recursive,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["compress", "extract"]


class UnsupportedArchiveTypeError(AssertionError):
    """Raise it if archive type is unsupported.

    It will not be catched outside.
    """


def extract_file(  # pylint: disable=too-many-branches # noqa: C901 PLR0912
    file: Path,
    dest: Path,
    compress_type: str = "gz",
    *,
    overwrite: bool = False,
) -> None:
    """Extract a compressed data file to destination.

    This function only supports gzip, bzip2 and xz compression which are
    only supports one-file compression.

    Args:
        file (Path): Path to compressed file.
        dest (Path): Destination directory.
        compress_type (str): Compression type. Default is "gz".
        overwrite (bool): Overwrite destination directory if it exists.

    Raises:
        UnsupportedArchiveTypeError: If compress is not in ["gz", "bz2", "xz"]

    """
    compress_type = compress_type.lower().strip()
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz"]:
        raise UnsupportedArchiveTypeError

    if compress_type == "gz":
        fsrc = gzip.open(file, "rb")  # noqa: SIM115
    elif compress_type == "bz2":
        fsrc = bz2.BZ2File(file, "rb")
    elif compress_type == "xz":
        fsrc = lzma.open(file, "rb")  # noqa: SIM115
    else:
        raise UnsupportedArchiveTypeError

    with fsrc:
        fsrc.seek(0, os.SEEK_END)
        fsize = fsrc.tell()
        fsrc.seek(0, os.SEEK_SET)
        if not overwrite:
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)
        with dest.open("wb") as fdst:
            if fsize > COPY_BUFSIZE * 50:
                task_start_msg = fast_format_str(
                    _(
                        "Extracting ${{file}} to ${{path}} as '${{type}}' ...",
                    ),
                    fmt={
                        "file": make_pretty(file),
                        "path": make_pretty(dest),
                        "type": compress_type,
                    },
                )
                task_name = _("Extracting")
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_start_msg=task_start_msg,
                    task_name=task_name,
                    total=fsize,
                )
                while buf := fsrc.read(COPY_BUFSIZE):
                    call_ktrigger(
                        IKernelTrigger.on_progress,
                        task_name=task_name,
                        current=len(buf),
                        delta=True,
                    )
                    fdst.write(buf)
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
            else:
                while buf := fsrc.read(COPY_BUFSIZE):
                    fdst.write(buf)


def _extract(
    compress_type: str,
    file: Path,
    dest: Path,
    password: str | None,
    *,
    overwrite: bool,
) -> None:
    if compress_type in ["gz", "gzip"]:
        logger.info("Extracting '%s' to '%s' as 'gz' ...", file, dest)
        extract_file(file, dest, "gz", overwrite=overwrite)
    elif compress_type in ["bz2", "bzip2"]:
        logger.info("Extracting '%s' to '%s' as 'bz2' ...", file, dest)
        extract_file(file, dest, "bz2", overwrite=overwrite)
    elif compress_type in ["xz", "lzma"]:
        logger.info("Extracting '%s' to '%s' as 'xz' ...", file, dest)
        extract_file(file, dest, "xz", overwrite=overwrite)
    elif compress_type == "zip":
        logger.info("Extracting '%s' to '%s' as 'zip' ...", file, dest)
        extract_zip(file, dest, password, overwrite=overwrite)
    elif compress_type in ["tar.gz", "tgz"]:
        logger.info("Extracting '%s' to '%s' as 'tar.gz' ...", file, dest)
        extract_tarball(file, dest, "gz", overwrite=overwrite)
    elif compress_type in ["tar.bz2", "tbz2"]:
        logger.info("Extracting '%s' to '%s' as 'tar.bz2' ...", file, dest)
        extract_tarball(file, dest, "bz2", overwrite=overwrite)
    elif compress_type in ["tar.xz", "txz"]:
        logger.info("Extracting '%s' to '%s' as 'tar.xz' ...", file, dest)
        extract_tarball(file, dest, "xz", overwrite=overwrite)
    elif compress_type == "tar":
        logger.info("Extracting '%s' to '%s' as 'tar' ...", file, dest)
        extract_tarball(file, dest, None, overwrite=overwrite)
    else:
        raise UnsupportedArchiveTypeError


def extract(  # pylint: disable=R0913 # noqa: PLR0913
    file: Path,
    dest: Path,
    compress_type: str | None = None,
    password: str | None = None,
    *,
    overwrite: bool = False,
    allow_absolute_dest: bool = False,
) -> None:
    """Extract compressed file to destination.

    Args:
        file (Path): Path to compressed file.
        dest (Path): Destination file or directory.
        compress_type (str | None, optional): Compression type. It can be "gz",
            "bz2", "xz", "zip", "tar.gz", "tar.bz2", "tar.xz" and "tar".
            Defaults to None.
        password (str | None, optional): Password to decrypt compressed file.
            Defaults to None. Tarball is not supported.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
        allow_absolute_dest (bool, optional): Allow absolute destination path.
            Defaults to False.

    """
    compress_type = compress_type.lower().strip() if compress_type else None
    if not allow_absolute_dest:
        assert_rel_path(dest)
    try:
        if compress_type is None:
            suffix1 = file.suffix
            suffix2 = file.suffixes[-2] if len(file.suffixes) > 1 else None
            if suffix2 == ".tar":
                compress_type = "tar" + suffix1
            elif suffix1:
                compress_type = suffix1[1:]
            else:
                raise RUValueError(
                    str(
                        fast_format_str(
                            _(
                                "Unable to guess compression type of ${{path}}.",  # noqa: E501
                            ),
                            fmt={"path": make_pretty(file)},
                        ),
                    ),
                    hint=_("Please specify the compression type explicitly."),
                )
        _extract(
            compress_type,
            file,
            dest,
            password,
            overwrite=overwrite,
        )
    except UnsupportedArchiveTypeError:
        logger.error(
            "Unsupported compression type: '%s'",
            compress_type,
        )
        raise RUValueError(
            fast_format_str(
                _("Unsupported compression type: ${{type}}"),
                fmt={"type": str(compress_type)},
            ),
            hint=_(
                "Supported types are 'gz', 'bz2', 'xz', 'zip', 'tar', "
                "'tar.gz', 'tar.bz2', 'tar.xz'. You can also use the 'tgz', "
                "'txz' and 'tbz2'.",
            ),
        ) from None
    except (
        tarfile.TarError,
        zipfile.BadZipfile,
        zipfile.LargeZipFile,
        lzma.LZMAError,
        OSError,
    ) as exc:
        logger.exception(
            "Failed to extract '%s' to '%s'.",
            file,
            dest,
        )
        raise RUValueError(
            fast_format_str(
                _("Failed to extract ${{file}} to ${{dest}}: ${{exc}}"),
                fmt={
                    "file": make_pretty(file),
                    "dest": make_pretty(dest),
                    "exc": str(exc),
                },
            ),
        ) from exc


def compress_file(  # pylint: disable=R0912 # noqa: C901 PLR0912
    src: Path,
    dest: Path,
    compress_type: str = "gz",
    compress_level: int | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Compress a file to destination.

    Args:
        src (Path): Source file.
        dest (Path): Destination file.
        compress_type (str): Compression type. Default is "gz".
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.

    """
    compress_type = compress_type.lower().strip()
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz"]:
        raise UnsupportedArchiveTypeError

    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)

    if compress_level is None:
        compress_level = 9

    if compress_type == "gz":
        fsrc = gzip.open(src, "rb", compresslevel=compress_level)  # noqa: SIM115
    elif compress_type == "bz2":
        fsrc = bz2.BZ2File(src, "rb", compresslevel=compress_level)
    elif compress_type == "xz":
        fsrc = lzma.open(src, "rb")  # noqa: SIM115
    else:
        raise UnsupportedArchiveTypeError

    with fsrc:
        fsrc.seek(0, os.SEEK_END)
        fsize = fsrc.tell()
        fsrc.seek(0, os.SEEK_SET)
        with dest.open("wb") as fdst:
            if fsize > COPY_BUFSIZE * 50:
                task_start_msg = fast_format_str(
                    _(
                        "Compressing ${{path}} to ${{file}} as '${{type}}' ...",
                    ),
                    fmt={
                        "path": make_pretty(src),
                        "file": make_pretty(dest),
                        "type": compress_type,
                    },
                )
                task_name = _("Compressing")
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_start_msg=task_start_msg,
                    task_name=task_name,
                    total=fsize,
                )
                while buf := fsrc.read(COPY_BUFSIZE):
                    call_ktrigger(
                        IKernelTrigger.on_progress,
                        task_name=task_name,
                        current=len(buf),
                        delta=True,
                    )
                    fdst.write(buf)
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
            else:
                while buf := fsrc.read(COPY_BUFSIZE):
                    fdst.write(buf)


def _compress(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_type: str | None = None,
    compress_level: int | None = None,
    *,
    overwrite: bool = False,
) -> None:
    if compress_type in ["gz", "gzip"]:
        logger.info("Compressing '%s' to '%s' as 'gz' ...", src, dest)
        compress_file(src, dest, "gz", compress_level, overwrite=overwrite)
    elif compress_type in ["bz2", "bzip2"]:
        logger.info("Compressing '%s' to '%s' as 'bz2' ...", src, dest)
        compress_file(src, dest, "bz2", compress_level, overwrite=overwrite)
    elif compress_type in ["xz", "lzma"]:
        logger.info("Compressing '%s' to '%s' as 'xz' ...", src, dest)
        compress_file(src, dest, "xz", compress_level, overwrite=overwrite)
    elif compress_type == "zip":
        logger.info("Compressing '%s' to '%s' as 'zip' ...", src, dest)
        compress_zip(
            src,
            dest,
            start,
            excludes,
            compress_level,
            overwrite=overwrite,
        )
    elif compress_type in ["tar.gz", "tgz"]:
        logger.info("Compressing '%s' to '%s' as 'tar.gz' ...", src, dest)
        compress_tarball(
            src,
            dest,
            start,
            excludes,
            "gz",
            compress_level,
            overwrite=overwrite,
        )
    elif compress_type in ["tar.bz2", "tbz2"]:
        logger.info("Compressing '%s' to '%s' as 'tar.bz2' ...", src, dest)
        compress_tarball(
            src,
            dest,
            start,
            excludes,
            "bz2",
            compress_level,
            overwrite=overwrite,
        )
    elif compress_type in ["tar.xz", "txz"]:
        logger.info("Compressing '%s' to '%s' as 'tar.xz' ...", src, dest)
        compress_tarball(
            src,
            dest,
            start,
            excludes,
            "xz",
            compress_level,
            overwrite=overwrite,
        )
    elif compress_type == "tar":
        logger.info("Compressing '%s' to '%s' as 'tar' ...", src, dest)
        compress_tarball(
            src,
            dest,
            start,
            excludes,
            None,
            None,
            overwrite=overwrite,
        )
    else:
        raise UnsupportedArchiveTypeError


def compress(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_type: str | None = None,
    compress_level: int | None = None,
    *,
    overwrite: bool = False,
    allow_absolute_dest: bool = False,
    cwd: Path | None = None,
) -> None:
    """Compress a file or directory to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        compress_type (str | None, optional): Compression type. It can be "gz",
            "bz2", "xz", "zip", "tar.gz", "tar.bz2", "tar.xz" and "tar".
            Defaults to None.
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
        allow_absolute_dest (bool, optional): Allow absolute destination path.
            Defaults to False.
        cwd (Path | None, optional): The working directory for compressing. For
            relative dest path. Defaults to None (don't chdir).

    """
    if cwd:
        old_cwd = Path.cwd()
        os.chdir(cwd)
    else:
        old_cwd = None
    compress_type = compress_type.lower().strip() if compress_type else None
    if not allow_absolute_dest:
        assert_rel_path(dest)
    try:
        if compress_type is None:
            suffix1 = dest.suffix
            suffix2 = dest.suffixes[-2] if len(dest.suffixes) > 1 else None
            if suffix2 == ".tar":
                compress_type = "tar" + suffix1
            elif suffix1:
                compress_type = suffix1[1:]
            else:
                raise RUValueError(
                    fast_format_str(
                        _(
                            "Unable to determine compression type of "  # -
                            "${{path}}.",
                        ),
                        fmt={"path": make_pretty(dest)},
                    ),
                    hint=_("Please specify the compression type explicitly."),
                )
        _compress(
            src,
            dest,
            start,
            excludes,
            compress_type,
            compress_level,
            overwrite=overwrite,
        )
    except UnsupportedArchiveTypeError:
        logger.error(
            "Unsupported compression type: '%s'",
            compress_type,
        )
        raise RUValueError(
            fast_format_str(
                _("Unsupported compression type: ${{type}}"),
                fmt={"type": str(compress_type)},
            ),
            hint=_(
                "Supported types are 'gz', 'bz2', 'xz', 'zip', 'tar', "
                "'tar.gz', 'tar.bz2', 'tar.xz'. You can also use the 'tgz', "
                "'txz' and 'tbz2'.",
            ),
        ) from None
    except (
        tarfile.TarError,
        zipfile.BadZipfile,
        zipfile.LargeZipFile,
        lzma.LZMAError,
        OSError,
    ) as exc:
        logger.exception(
            "Failed to compress '%s' to '%s'.",
            src,
            dest,
        )
        raise RUValueError(
            fast_format_str(
                _("Failed to compress ${{src}} to ${{dest}}: ${{exc}}"),
                fmt={
                    "src": make_pretty(src),
                    "dest": make_pretty(dest),
                    "exc": str(exc),
                },
            ),
        ) from exc
    finally:
        if old_cwd:
            os.chdir(old_cwd)
