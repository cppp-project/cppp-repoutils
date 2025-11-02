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

"""Package management utils for environment."""

from __future__ import annotations

import contextlib
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast

import json5

from rubisco.config import (
    DEFAULT_CHARSET,
    EXTENSIONS_DIR,
    RUBP_LICENSE_FILE_NAME,
    RUBP_METADATA_FILE_NAME,
    RUBP_README_FILE_NAME,
    RUBP_REQUIREMENTS_FILE_NAME,
    RUBP_RESOURCE_DIR_NAME,
)
from rubisco.envutils.env_type import EnvType
from rubisco.envutils.pip import install_requirements
from rubisco.envutils.utils import canonical_pkg_name
from rubisco.kernel.ext_name_check import is_valid_extension_name
from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.lib.archive import extract_zip
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import TemporaryObject, rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import get_dict_check, type_assert
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import iter_assert, make_pretty
from rubisco.lib.version import Version
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from collections.abc import Callable

    from rubisco.envutils.env import RUEnvironment


__all__ = [
    "ExtensionPackageInfo",
    "get_extension_package_info",
    "install_extension",
    "query_packages",
    "uninstall_extension",
    "upgrade_extension",
]


@dataclass
class ExtensionPackageInfo:  # pylint: disable=too-many-instance-attributes
    """Extension package info."""

    name: str
    version: Version
    description: str
    homepage: str
    maintainers: list[str]
    pkg_license: str
    tags: list[str]
    requirements: str | None
    env_type: EnvType

    def __hash__(self) -> int:
        """Return the hash of the package name."""
        return hash(self.name)


def _pkg_check(zip_file: zipfile.ZipFile, pkg_name: str) -> None:
    files = zip_file.namelist()
    root_list: set[str] = set()
    for file in files:
        if Path(file).parts:
            root_list.add(str(Path(file).parts[0]))

    try:
        root_list.remove(canonical_pkg_name(pkg_name))
        root_list.remove(RUBP_METADATA_FILE_NAME)
    except KeyError as exc:
        raise RUValueError(
            fast_format_str(
                _(
                    "'${{name}}' package must contain a directory with the "
                    "same name as the package name and a '${{metafile}}' file.",
                ),
                fmt={"name": pkg_name, "metafile": RUBP_METADATA_FILE_NAME},
            ),
        ) from exc
    with contextlib.suppress(KeyError):
        root_list.remove(RUBP_LICENSE_FILE_NAME)
    with contextlib.suppress(KeyError):
        root_list.remove(RUBP_README_FILE_NAME)
    with contextlib.suppress(KeyError):
        root_list.remove(RUBP_REQUIREMENTS_FILE_NAME)
    with contextlib.suppress(KeyError):
        root_list.remove(RUBP_RESOURCE_DIR_NAME)

    if root_list:
        raise RUValueError(
            fast_format_str(
                _(
                    "'${{name}}' package contains files that not allowed in "
                    "the root directory.",
                ),
                fmt={"name": pkg_name},
            ),
        )


def parse_extension_info(
    config_file: IO[str] | IO[bytes],
    file_name: str = RUBP_METADATA_FILE_NAME,
) -> ExtensionPackageInfo:
    """Parse the extension package info from the config file.

    Args:
        config_file (IO[str] | IO[bytes]): The config file.
        file_name (str, optional): The file name. For error message.
            Defaults to RUBP_METADATA_FILE_NAME.

    Returns:
        ExtensionPackageInfo: The extension package info.
            The `requirements` field will be None always.

    Raises:
        RUValueError: If the config file is not a valid JSON5 file.
            Or some mandatory fields are missing (KeyError).

    """
    _file_text = config_file.read()
    if isinstance(_file_text, bytes):
        file_text = _file_text.decode(DEFAULT_CHARSET)
    else:
        file_text = str(_file_text)
    try:
        pkg_config = cast(
            "dict[str, object]",
            type_assert(json5.loads(file_text), dict[str, object]),
        )
        pkg_name = cast("str", get_dict_check(pkg_config, "name", str))
        if not is_valid_extension_name(pkg_name):
            raise RUValueError(
                fast_format_str(
                    _(
                        "Package name '${{name}}' invalid.",
                    ),
                    fmt={"name": pkg_name},
                ),
                hint=_(
                    "Package name must be lowercase and only contain "
                    "0-9, a-z, A-Z, '_', '.' and '-'.",
                ),
            )
        maintianers = [
            Maintainer.parse(x)
            for x in cast(
                "list[dict[str, str | None]]",
                get_dict_check(pkg_config, "maintainers", list[dict[str, str]]),
            )
        ]
        tags = cast(
            "list[str]",
            get_dict_check(pkg_config, "tags", list[str]),
        )
        pattern = re.compile(r"^[a-z0-9_-]+$")
        iter_assert(
            tags,
            lambda x: re.match(pattern, x) is not None,
            RUValueError(
                _(
                    "Tags must be lowercase and only contain 0-9, a-z, A-Z"
                    ", '_' and '-'.",
                ),
            ),
        )

        return ExtensionPackageInfo(
            pkg_name,
            Version(str(get_dict_check(pkg_config, "version", str))),
            str(get_dict_check(pkg_config, "description", str)),
            str(get_dict_check(pkg_config, "homepage", str)),
            [str(x) for x in maintianers],
            str(get_dict_check(pkg_config, "license", str)),
            tags,
            None,
            EnvType.FOREIGN,
        )
    except json5.JSON5DecodeError as exc:
        raise RUValueError(
            fast_format_str(
                _(
                    "${{path}} package configuration "
                    "file is not a valid JSON5 file.",
                ),
                fmt={"path": make_pretty(file_name)},
            ),
        ) from exc
    except KeyError as exc:
        raise RUValueError(
            fast_format_str(
                _(
                    "${{path}} package configuration "
                    "file is missing a required key: ${{key}}.",
                ),
                fmt={"path": make_pretty(file_name), "key": exc.args[0]},
            ),
        ) from exc


def get_extension_package_info(pkg_file: Path) -> ExtensionPackageInfo:
    """Get the extension package info.

    Args:
        pkg_file (Path): The package file.

    Returns:
        ExtensionPackageInfo: The extension package info.

    """
    json_opened = False
    try:
        with (
            zipfile.ZipFile(pkg_file, "r") as zip_file,
            zip_file.open(RUBP_METADATA_FILE_NAME) as package_file,
        ):
            json_opened = True
            ext_info = parse_extension_info(package_file)

            _pkg_check(zip_file, ext_info.name)

            try:
                with zip_file.open(RUBP_REQUIREMENTS_FILE_NAME) as req_file:
                    requirements = req_file.read().decode(DEFAULT_CHARSET)
            except KeyError:
                requirements = None

            ext_info.requirements = requirements

            return ext_info
    except zipfile.error as exc:
        raise RUValueError(
            fast_format_str(
                _(
                    "${{path}} is not a valid Rubisco extension package.",
                ),
                fmt={"path": make_pretty(pkg_file)},
            ),
            hint=_("Rubisco extension package must be a zip file."),
        ) from exc
    except KeyError as exc:
        # If meta file not found, ZipFile.open raises KeyError.
        if not json_opened:
            raise RUValueError(
                fast_format_str(
                    _(
                        "Error while opening ${{metafile}} in ${{path}}: "
                        "'${{msg}}'.",
                    ),
                    fmt={
                        "path": make_pretty(pkg_file),
                        "metafile": make_pretty(RUBP_METADATA_FILE_NAME),
                        "msg": exc.args[0],
                    },
                ),
            ) from exc
        raise RUValueError(
            fast_format_str(
                _(
                    "${{path}} package configuration "
                    "file is missing a required key: '${{key}}'.",
                ),
                fmt={"path": make_pretty(pkg_file), "key": exc.args[0]},
            ),
        ) from exc


_EIS_NOT_INSTALLED = 0
_EIS_LOWER_VERSION = 1
_EIS_SAME_VERSION = 2
_EIS_HIGHER_VERSION = 3


def _ext_is_installed(
    name: str,
    dest: RUEnvironment,
    cur_version: Version,
) -> int:
    """Check for the extension installation status.

    Return 0 if the extension is not installed, 1 if lower version, 2 if
    same version and 3 if higher version.
    """
    installed_exts = dest.db_handle.query_packages([name])
    if len(installed_exts) > 1:
        logger.warning("Multiple instances of '%s' extension found.", name)
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Multiple instances of '${{name}}' extension"
                    " found in the database. Selecting the last one.",
                ),
                fmt={"name": name},
            ),
        )
    elif not installed_exts:
        return _EIS_NOT_INSTALLED

    installed_ext = installed_exts.pop()

    if installed_ext.version < cur_version:
        return _EIS_LOWER_VERSION
    if installed_ext.version == cur_version:
        return _EIS_SAME_VERSION
    return _EIS_HIGHER_VERSION


def _extract_extension(
    info: ExtensionPackageInfo,
    pkg_file: Path,
    dest: RUEnvironment,
    callback: Callable[[TemporaryObject, TemporaryObject], None],
) -> None:
    """Extract the extension package to the destination directory."""
    with (
        TemporaryObject.register_tempobject(
            dest.path / EXTENSIONS_DIR / canonical_pkg_name(info.name),
            TemporaryObject.TYPE_DIRECTORY,
        ) as dest_dir,
        TemporaryObject.new_directory() as temp_dir,
    ):
        extract_zip(pkg_file, temp_dir.path / "data")
        if (temp_dir.path / "data" / RUBP_REQUIREMENTS_FILE_NAME).exists():
            install_requirements(
                dest,
                temp_dir.path / "data" / RUBP_REQUIREMENTS_FILE_NAME,
            )
            shutil.move(
                (temp_dir.path / "data" / RUBP_REQUIREMENTS_FILE_NAME),
                dest_dir.path / RUBP_REQUIREMENTS_FILE_NAME,
            )
        shutil.move(
            temp_dir.path / "data" / canonical_pkg_name(info.name),
            dest_dir.path,
        )
        if (temp_dir.path / "data" / RUBP_LICENSE_FILE_NAME).exists():
            shutil.move(
                temp_dir.path / "data" / RUBP_LICENSE_FILE_NAME,
                dest_dir.path / RUBP_LICENSE_FILE_NAME,
            )
        if (temp_dir.path / "data" / RUBP_README_FILE_NAME).exists():
            shutil.move(
                temp_dir.path / "data" / RUBP_README_FILE_NAME,
                dest_dir.path / RUBP_README_FILE_NAME,
            )
        if (temp_dir.path / "data" / RUBP_RESOURCE_DIR_NAME).exists():
            shutil.move(
                temp_dir.path / "data" / RUBP_RESOURCE_DIR_NAME,
                dest_dir.path / RUBP_RESOURCE_DIR_NAME,
            )
        # Register the extension.
        callback(dest_dir, temp_dir)
        dest_dir.move()  # Release the ownership. Make it permanent.


def _install_extension(
    pkg_file: Path,
    info: ExtensionPackageInfo,
    dest: RUEnvironment,
) -> None:
    if (dest.path / EXTENSIONS_DIR / info.name).exists():
        raise RUValueError(
            fast_format_str(
                _(
                    "${{path}} already exists in the filesystem.",
                ),
                fmt={
                    "path": make_pretty(dest.path / EXTENSIONS_DIR / info.name),
                },
            ),
        )

    def _callback(
        _dest_dir: TemporaryObject,
        _temp_dir: TemporaryObject,
    ) -> None:
        dest.db_handle.add_packages([info])

    _extract_extension(info, pkg_file, dest, _callback)


def query_packages(
    pkg_names: list[str],
    dest: RUEnvironment | list[RUEnvironment],
) -> set[ExtensionPackageInfo]:
    """Query the extension package.

    Args:
        pkg_names (list[str]): The package names or match patterns.
        dest (RUEnvironment | list[RUEnvironment]): The destination environment.
            Pass a list of environments to query multiple environments.

    Returns:
        set[ExtensionPackageInfo]: The extension package info.

    """
    query: set[ExtensionPackageInfo] = set()
    logger.info(
        "Querying extension packages %s ... in %s",
        pkg_names,
        str(dest),
    )

    # Don't use RUEnvrionment avoid recursive import.
    if not isinstance(dest, list):
        dest = [dest]

    for pattern in pkg_names:
        for env in dest:
            query |= env.db_handle.query_packages([pattern])
    if not query:
        if pkg_names == [".*"]:
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=_(
                    "No extension installed.",
                ),
            )
        else:
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _(
                        "No extension found matching '${{pattern}}'.",
                    ),
                    fmt={"pattern": ", ".join(pkg_names)},
                ),
            )
        return set()
    if len(query) > 1:
        for package in query:
            call_ktrigger(
                IKernelTrigger.on_hint,
                message=fast_format_str(
                    _("Selected '${{name}}'."),
                    fmt={"name": package.name},
                ),
            )
    return query


def _uninstall_extension(
    epi: ExtensionPackageInfo,
    dest: RUEnvironment,
) -> None:
    # Remove it from the database first.
    dest.db_handle.remove_packages([epi])
    path = dest.path / EXTENSIONS_DIR / canonical_pkg_name(epi.name)
    try:
        rm_recursive(path)
    except FileNotFoundError:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Extension '${{name}}'(${{path}}) is not found in the "
                    "filesystem.",
                ),
                fmt={
                    "name": epi.name,
                    "path": make_pretty(path),
                },
            ),
        )
    except:
        dest.db_handle.rollback()
        raise


def uninstall_extension(pkg_names: list[str], dest: RUEnvironment) -> None:
    """Uninstall the extension package.

    Args:
        pkg_names (list[str]): The package names.
        dest (RUEnvironment): The destination environment.

    """
    with dest:
        query = query_packages(pkg_names, dest)
        if not query:
            return

        logger.info(
            "Uninstalling extension packages '%s'... in %s",
            query,
            str(dest),
        )

        try:
            call_ktrigger(
                IKernelTrigger.on_verify_uninstall_extension,
                dest=dest,
                query=query,
            )
        except KeyboardInterrupt:
            logger.info("User interrupted the uninstallation.")
            call_ktrigger(
                IKernelTrigger.on_error,
                message=_("Interrupted by user."),
            )
            return

        for package in query:
            call_ktrigger(
                IKernelTrigger.on_uninstall_extension,
                dest=dest,
                ext_name=package.name,
                ext_version=package.version,
            )
            _uninstall_extension(package, dest)
            call_ktrigger(
                IKernelTrigger.on_extension_uninstalled,
                dest=dest,
                ext_name=package.name,
                ext_version=package.version,
            )


def upgrade_extension(pkg_file: Path, dest: RUEnvironment) -> None:
    """Upgrade the extension package.

    Args:
        pkg_file (Path): The package file.
        dest (RUEnvironment): The destination environment.

    """
    info = get_extension_package_info(pkg_file)
    with dest:
        eis = _ext_is_installed(info.name, dest, info.version)
        if eis == _EIS_NOT_INSTALLED:
            install_extension(pkg_file, dest)
            return
        if eis == _EIS_SAME_VERSION:
            call_ktrigger(
                IKernelTrigger.on_hint,
                message=fast_format_str(
                    _(
                        "The same version of '${{name}}' extension is "
                        "already installed.",
                    ),
                    fmt={"name": info.name},
                ),
            )
            return
        if eis == _EIS_HIGHER_VERSION:
            call_ktrigger(
                IKernelTrigger.on_hint,
                message=fast_format_str(
                    _(
                        "The higher version of '${{name}}' extension is "
                        "already installed.",
                    ),
                    fmt={"name": info.name},
                ),
            )
            return

        call_ktrigger(
            IKernelTrigger.on_upgrade_extension,
            dest=dest,
            ext_name=info.name,
            ext_version=info.version,
        )

        _uninstall_extension(info, dest)
        _install_extension(pkg_file, info, dest)

        call_ktrigger(
            IKernelTrigger.on_extension_upgraded,
            dest=dest,
            ext_name=info.name,
            ext_version=info.version,
        )


def install_extension(pkg_file: Path, dest: RUEnvironment) -> None:
    """Install the Rubisco binary package (RuBP).

    Args:
        pkg_file (Path): The package file. It's a zip file with "rubp" suffix.
        dest (RUEnvironment): The destination environment.

    """
    if pkg_file.suffix not in {".rubp", ".RuBP"}:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Rubisco Binary Package (RuBP) '${{path}}' must be a zip"
                    "file with '.rubp' suffix.",
                ),
                fmt={"path": pkg_file},
            ),
        )

    info = get_extension_package_info(pkg_file)
    with dest:
        # EIS: Extension Installation Status.
        eis = _ext_is_installed(info.name, dest, info.version)
        if eis == _EIS_LOWER_VERSION:
            upgrade_extension(pkg_file, dest)
        elif eis == _EIS_SAME_VERSION:
            call_ktrigger(
                IKernelTrigger.on_hint,
                message=fast_format_str(
                    _(
                        "The same version of '${{name}}' extension is "
                        "already installed.",
                    ),
                    fmt={"name": info.name},
                ),
            )
            return
        elif eis == _EIS_HIGHER_VERSION:
            call_ktrigger(
                IKernelTrigger.on_hint,
                message=fast_format_str(
                    _(
                        "The higher version of '${{name}}' extension is "
                        "already installed.",
                    ),
                    fmt={"name": info.name},
                ),
            )
            return

        call_ktrigger(
            IKernelTrigger.on_install_extension,
            dest=dest,
            ext_name=info.name,
            ext_version=info.version,
        )

        _install_extension(pkg_file, info, dest)

        call_ktrigger(
            IKernelTrigger.on_extension_installed,
            dest=dest,
            ext_name=info.name,
            ext_version=info.version,
        )
