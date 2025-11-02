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

"""Rubisco extensions interface."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

import beartype

from rubisco.config import (
    DEFAULT_CHARSET,
    GLOBAL_EXTENSIONS_VENV_DIR,
    RUBP_METADATA_FILE_NAME,
    USER_EXTENSIONS_VENV_DIR,
    WORKSPACE_EXTENSIONS_VENV_DIR,
)
from rubisco.envutils.env import (
    GLOBAL_ENV,
    USER_ENV,
    WORKSPACE_ENV,
    RUEnvironment,
)
from rubisco.envutils.packages import ExtensionPackageInfo, parse_extension_info
from rubisco.envutils.utils import canonical_pkg_name
from rubisco.kernel.config_file import config_file
from rubisco.kernel.ext_name_check import is_valid_extension_name
from rubisco.kernel.workflow import register_step_type
from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.lib.exceptions import RUNotRubiscoExtensionError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.load_module import import_module_from_path
from rubisco.lib.log import logger
from rubisco.lib.typecheck import get_dict_check
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    bind_ktrigger_interface,
    call_ktrigger,
)

if TYPE_CHECKING:
    from rubisco.kernel.workflow.step import Step

__all__ = [
    "IRUExtension",
    "find_extension",
    "load_extension",
]


class IRUExtension(abc.ABC):
    """Rubisco extension interface."""

    # These attributes are provided by extension.
    ktrigger: IKernelTrigger
    workflow_steps: ClassVar[dict[str, type[Step]]]
    steps_contributions: ClassVar[dict[type[Step], list[str]]]

    # These attributes are provided by Rubisco.
    resdir: Path  # Resource directory. (if exists)

    @abc.abstractmethod
    def extension_can_load_now(self) -> bool:
        """Check if the extension can load now.

        Some extensions may initialize
        optionally like 'CMake' or 'Rust'.

        This method MUST be implemented by the subclass.

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the extension can load now, otherwise False.

        """

    @abc.abstractmethod
    def on_load(self) -> None:
        """Load the extension.

        Initialize the extension here.
        This method MUST be implemented by the subclass.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def reqs_is_solved(self) -> bool:
        """Check if the system requirements are solved.

        This method should return True if the system requirements are solved,
        otherwise False.

        This method MUST be implemented by the subclass.

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the system requirements are solved, otherwise False.

        """

    @abc.abstractmethod
    def solve_reqs(self) -> None:
        """Solve the system requirements.

        This method MUST be implemented by the subclass.
        If the slution is not possible, please raise an exception here.
        It is recommended to use RUError if you have hint, docurl, etc.
        """


@beartype.beartype
def find_extension(name: str) -> Path:
    """Find the extension by name.

    Args:
        name (str): Find the extension by name.

    Raises:
        RUValueError: Raise if the extension is not found.

    """
    if (WORKSPACE_EXTENSIONS_VENV_DIR / name).is_dir():
        path = GLOBAL_EXTENSIONS_VENV_DIR / name
    elif (USER_EXTENSIONS_VENV_DIR / name).is_dir():
        path = USER_EXTENSIONS_VENV_DIR / name
    elif (GLOBAL_EXTENSIONS_VENV_DIR / name).is_dir():
        path = WORKSPACE_EXTENSIONS_VENV_DIR / name
    else:
        raise RUValueError(
            fast_format_str(
                _(
                    "The extension '${{name}}' does not exist in"
                    " workspace, user, or global extension directory.",
                ),
                fmt={"name": name},
            ),
            hint=fast_format_str(_("Try to load the extension as a path.")),
        )
    return path


INVALID_EXT_NAMES = ["rubisco"]  # Avoid logger's name conflict.


def _get_extension_instance(path: Path, ext_name: str) -> IRUExtension:
    try:
        module = import_module_from_path(path / ext_name)
    except RUNotRubiscoExtensionError as exc:
        raise RUValueError(
            fast_format_str(
                _(
                    "The extension path ${{path}} does not exist.",
                ),
                fmt={"path": make_pretty(Path(exc.args[0]).absolute())},
            ),
        ) from exc

    if not hasattr(module, "instance"):
        raise RUValueError(
            fast_format_str(
                _(
                    "The extension ${{path}} does not have an instance.",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
            hint=fast_format_str(
                _(
                    "Please make sure this extension is valid.",
                ),
            ),
        )
    instance: IRUExtension = module.instance

    # Pass attributes to the extension.
    instance.resdir = path / "res"

    return instance


def _solve_extension_reqs(instance: IRUExtension, ext_name: str) -> None:
    if not instance.reqs_is_solved():
        logger.info(
            "Solving requirements for extension '%s'...",
            ext_name,
        )
        instance.solve_reqs()
        if not instance.reqs_is_solved():
            logger.error(
                "Failed to solve requirements for extension '%s'.",
                ext_name,
            )


def _get_ext_info(
    ext: Path | str | ExtensionPackageInfo,
    env: RUEnvironment,
) -> tuple[Path, ExtensionPackageInfo]:
    if isinstance(ext, Path) or (isinstance(ext, str) and Path(ext).is_dir()):
        ext_ = Path(ext)
        # If it's a standalone extension, we need to load the
        # meta file to get the extension info.
        with (ext_ / RUBP_METADATA_FILE_NAME).open(
            "r",
            encoding=DEFAULT_CHARSET,
        ) as file:
            ext_info = parse_extension_info(file, str(config_file))
        return ext_, ext_info

    if isinstance(ext, str):
        # If path is str, treat it as the name of the extension.
        ext = find_extension(ext)
        ext_info = env.db_handle.get_package(ext.name)
        return ext, ext_info

    ext_info = ext
    return (
        env.extensions_venv_path / canonical_pkg_name(ext_info.name),
        ext_info,
    )


loaded_extensions: list[str] = []


# A basic extension contains these modules or variables:
#   - extension/        directory    ---- The extension directory.
#       - __init__.py   file         ---- The extension module.
#           - instance  IRUExtension ---- The extension instance
@beartype.beartype
def load_extension(
    ext: Path | str | ExtensionPackageInfo,
    env: RUEnvironment,
    *,
    strict: bool = False,
) -> None:
    """Load the extension.

    Args:
        ext (Path | str | ExtensionPackageInfo):If it is a str, it will be
            treat as extension's name, the extension will be loaded from the
            default extension directory. If the path is a path, the extension
            will be loaded from the path. If the path is ExtensionPackageInfo
            type, the extension will be loaded from the package info.
        env (RUEnvironment): The environment of the extension.
            It will be used only if the extension is a installed extension.
            If the extension is a standalone extension, it will be ignored.
            We will get the extension's info from the meta file.
        strict (bool, optional): If True, raise an exception if the extension
            loading failed.

    """
    try:
        path, ext_info = _get_ext_info(ext, env)

        if ext_info.name in loaded_extensions:
            logger.info("Extension '%s' already loaded.", ext_info.name)
            return

        # Security check.
        if not is_valid_extension_name(ext_info.name):
            raise RUValueError(  # noqa: TRY301
                fast_format_str(
                    _(
                        "Extension name '${{name}}' invalid.",
                    ),
                    fmt={"name": ext_info.name},
                ),
                hint=_(
                    "Extension name must be lowercase and only contain "
                    "0-9, a-z, A-Z, '_', '.' and '-'.",
                ),
            )

        logger.info("Loading extension '%s'...", ext_info.name)

        # Get the extension instance.
        instance = _get_extension_instance(
            path,
            canonical_pkg_name(ext_info.name),
        )

        # Check if the extension can load now.
        if not instance.extension_can_load_now():
            logger.info("Skipping extension '%s'...", ext_info.name)
            return

        # Load the extension.
        _solve_extension_reqs(instance, ext_info.name)

        # Register the workflow steps.
        for step_name, step in instance.workflow_steps.items():
            contributions = []
            if step in instance.steps_contributions:
                contributions = instance.steps_contributions[step]
            register_step_type(step_name, step, contributions)

        # Load the extension.
        instance.on_load()

        # Bind the extension's ktrigger.
        bind_ktrigger_interface(
            ext_info.name,
            instance.ktrigger,
        )
        call_ktrigger(
            IKernelTrigger.on_extension_loaded,
            instance=instance,
            ext_info=ext_info,
        )

        loaded_extensions.append(ext_info.name)
        logger.info("Loaded extension: %s", ext_info.name)
    except Exception as exc:  # pylint: disable=broad-except
        if strict:
            raise exc from None
        logger.exception("Failed to load extension '%s': %s", ext, exc)
        # Report the error as error but don't raise it.
        strext = (
            str(ext.name)
            if isinstance(
                ext,
                ExtensionPackageInfo,
            )
            else str(ext)
        )
        call_ktrigger(
            IKernelTrigger.on_error,
            message=fast_format_str(
                _("Failed to load extension '${{env}}/${{name}}': ${{exc}}"),
                fmt={
                    "env": env.env_type.value,
                    "name": strext,
                    "exc": str(exc),
                },
            ),
        )


def _load_exts(env: RUEnvironment, autoruns: list[str]) -> None:
    try:
        for ext in env.db_handle.get_all_packages():
            if ext.name in autoruns:
                load_extension(ext, env)
    except OSError as exc:
        logger.warning("Failed to load extensions from '%s': %s", env, exc)


def load_all_extensions() -> None:
    """Load all extensions."""
    autoruns = cast(
        "list[str]",
        get_dict_check(
            config_file.config,
            "autoruns",
            valtype=list[str],
            default=[],
        ),
    )
    autoruns = list(set(autoruns))

    logger.info("Trying to load all extensions: %s ...", autoruns)

    if WORKSPACE_ENV.exists():
        _load_exts(WORKSPACE_ENV, autoruns)
    if USER_ENV.exists():
        _load_exts(USER_ENV, autoruns)
    if GLOBAL_ENV.exists():
        _load_exts(GLOBAL_ENV, autoruns)


WorkflowInterfaces.set_load_extension(load_extension)  # Avoid circular import.
