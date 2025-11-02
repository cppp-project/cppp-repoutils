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

"""Rubisco command event args and options class."""

from dataclasses import dataclass, field

from rubisco.lib.exceptions import RUTypeError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.typecheck import is_instance
from rubisco.lib.variable.fast_format_str import fast_format_str

__all__ = ["Argument", "DynamicArguments", "Option", "load_callback_args"]


@dataclass
class OptionOrArgument[T]:  # pylint: disable=R0902
    """Option or argument class.

    This is the base class for option and argument. It is used to store the
    information of an option or argument.

    """

    name: str  # Used in CLI.
    title: str  # Used in GUI. It maybe unused forever.
    description: str
    typecheck: type[T]

    # Option's aliases, Used in CLI.
    aliases: list[str] = field(default_factory=list[str])
    default: T | None = None

    ext_attributes: dict[str, object] = field(default_factory=dict[str, object])

    _value: T | None = None

    _is_option: bool = False
    _frozen: bool = False

    def get(self) -> T:
        """Get the value.

        Returns:
            T: The value.

        Raises:
            RUTypeError: If the value is not the given type.
            RUValueError: If the value is not set.

        """
        if self._value is None:
            if self.default is not None:
                return self.default
            if self._is_option:
                msg = _("Missing required option: ${{name}}.")
            else:
                msg = _("Missing required argument: ${{name}}.")
            raise RUValueError(
                fast_format_str(msg, fmt={"name": self.name}),
            )
        if not is_instance(self._value, self.typecheck):
            if self._is_option:
                msg = _("The option `${{name}}` is not the type `${{type}}`.")
            else:
                msg = _("The argument `${{name}}` is not the type `${{type}}`.")
            raise RUTypeError(
                fast_format_str(
                    msg,
                    fmt={
                        "name": self.name,
                        "type": self.typecheck.__name__,
                    },
                ),
            )
        return self._value

    def set(self, value: T) -> None:
        """Set the value.

        Args:
            value (T): The value.

        Raises:
            RUValueError: If the value is frozen.
            RUTypeError: If the value is not the given type.

        """
        if not is_instance(value, self.typecheck):
            if self._is_option:
                msg = _("The option `${{name}}` is not the type `${{type}}`.")
            else:
                msg = _("The argument `${{name}}` is not the type `${{type}}`.")
            raise RUTypeError(
                fast_format_str(
                    msg,
                    fmt={
                        "name": self.name,
                        "type": self.typecheck.__name__,
                    },
                ),
            )
        if self._frozen:
            if self._is_option:
                msg = _("The option `${{name}}` is readonly now.")
            else:
                msg = _("The argument `${{name}}` is readonly now.")
            raise RUValueError(
                fast_format_str(
                    msg,
                    fmt={"name": self.name},
                ),
            )

        logger.debug(
            "Set %s %s to %s.",
            "option" if self._is_option else "argument",
            self.name,
            value,
        )
        self._value = value

    @property
    def value(self) -> T:
        """Get the value.

        Returns:
            T: The value.

        Raises:
            RUTypeError: If the value is not the given type.
            RUValueError: If the value is not set.

        """
        return self.get()

    @value.setter
    def value(self, value: T) -> None:
        """Set the value.

        Args:
            value (T): The value.

        Raises:
            RUValueError: If the value is frozen.

        """
        self.set(value)

    def freeze(self) -> None:
        """Freeze the value.

        After freezing, the value cannot be changed.
        """
        self._frozen = True

    def unfreeze(self) -> None:
        """Unfreeze the value.

        After unfreezing, the value can be changed.
        """
        self._frozen = False


class Option[T](OptionOrArgument[T]):  # pylint: disable=R0903
    """Option class.

    Options is a key-value pair. It is used to pass non-positional and named
    arguments to a command event. Use `set_option` to set the value of an
    command event option. Options can be passed in each level.

    In CLI, options are prefixed with dash (-) or double-dash (--). For example,
    `ru --debug ext show -w` means the command event `/ext/show` will be called
    and the option `debug` in **the first level** (`/`) will be set to `True`,
    and the option `w` in **the third level** (`/ext/show`) will be set to
    `True`.

    """

    def __post_init__(self) -> None:
        """Post init."""
        self._is_option = True


@dataclass
class Argument[T](OptionOrArgument[T]):
    """Argument class.

    Arguments is a positional argument. It is used to pass positional arguments
    to a command event. Arguments of a command event cannot be set partially. It
    must be passed in the top level.

    In CLI, arguments are passed in the order of the command event's arguments
    definition. For example, `ru ext show 1 2 3` means the command event
    `/ext/show` will be called and the arguments `1`, `2`, `3` will be passed
    to the command event.

    """

    def __post_init__(self) -> None:
        """Post init."""
        self._is_option = False


@dataclass
class DynamicArguments:  # pylint: disable=R0902
    """Dynamic arguments.

    Some command events may have dynamic arguments. This class is used to
    define the dynamic arguments.

    """

    name: str  # Used in CLI.
    title: str  # Used in GUI.
    description: str
    mincount: int
    maxcount: int = -1
    ext_attributes: dict[str, object] = field(default_factory=dict[str, object])

    _value: list[Argument[str]] | None = field(
        default_factory=list[Argument[str]],
    )

    _frozen: bool = False

    def __post_init__(self) -> None:
        """Post init."""
        if self.mincount < 0:
            msg = fast_format_str(
                _(
                    "The minimum count of `${{name}}` must be greater "
                    "than or equal to 0.",
                ),
                fmt={"name": self.name},
            )
            raise RUValueError(msg)
        if self.maxcount != -1 and self.maxcount <= self.mincount:
            raise RUValueError(
                fast_format_str(
                    _(
                        "The maximum count of `${{name}}` must be greater "
                        "than the minimum count of `${{name}}`.",
                    ),
                    fmt={"name": self.name},
                ),
            )

    def get(self) -> list[Argument[str]] | None:
        """Get the argument list.

        Returns:
            list[Argument[str]]: The list that contains the arguments.

        """
        return self._value

    def set(self, value: list[Argument[str]]) -> None:
        """Get the arguments.

        Args:
            value (list[Argument[str]]): The arguments.

        """
        if self._frozen:
            msg = _("The argument `${{name}}` is readonly now.")
            raise RUValueError(
                fast_format_str(
                    msg,
                    fmt={"name": self.name},
                ),
            )

        self._value = value

    @property
    def value(self) -> list[Argument[str]] | None:
        """Get the argument list.

        Returns:
            list[Argument[str]]: The list that contains the arguments.

        """
        return self.get()

    @value.setter
    def value(self, value: list[Argument[str]]) -> None:
        """Get the arguments.

        Args:
            value (list[Argument[str]]): The arguments.

        """
        self.set(value)

    def freeze(self) -> None:
        """Freeze the value.

        After freezing, the value cannot be changed.
        """
        self._frozen = True

    def unfreeze(self) -> None:
        """Unfreeze the value.

        After unfreezing, the value can be changed.
        """
        self._frozen = False


def load_callback_args[OT, AT](
    options: list[Option[OT]],
    args: list[Argument[AT]],
) -> tuple[dict[str, OT], list[AT]]:
    """Load callback arguments.

    Args:
        options (list[Option[OT]]): List of options.
        args (list[Argument[AT]]): List of arguments.

    Returns:
        tuple[dict[str, OT], list[AT]]: A tuple of options and arguments.

    """
    opt_dict: dict[str, OT] = {}
    for opt in options:
        opt_dict[opt.name] = opt.value

    return opt_dict, [arg.get() for arg in args]
