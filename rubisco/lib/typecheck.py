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

"""Check types of variables with substitution support."""

import warnings
from types import EllipsisType, GenericAlias, UnionType
from typing import Any, cast, get_args, get_origin

from beartype import beartype

from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str

__all__ = [
    "ValType",
    "get_dict_check",
    "get_list_check",
    "is_instance",
    "rubisco_isinstance",
    "type_assert",
]

type ValType[T] = type[object | T] | GenericAlias | UnionType | None


def rubisco_isinstance(obj: object, objtype: type | UnionType) -> bool:
    """Check if an object is an instance of a type.

    Args:
        obj (object): Object to check.
        objtype (type | UnionType): Type to check against.

    Returns:
        bool: True if obj is an instance of objtype, False otherwise.

    """
    # Check aliases.
    if objtype is Any or objtype is object:
        return True

    return isinstance(obj, objtype)


def _is_instance_generic_alias_dict(
    obj: dict[Any, Any],
    args: tuple[Any, ...],
) -> bool:
    if len(args) != 2:  # noqa: PLR2004
        msg = "Invalid generic type"
        raise TypeError(msg)
    keytype, valtype = args
    keytype: type | GenericAlias | UnionType | None
    valtype: type | GenericAlias | UnionType | None

    if hasattr(obj, "items") and callable(
        obj.items,
    ):
        return all(
            is_instance(key, keytype) and is_instance(val, valtype)
            for key, val in obj.items()
        )

    return False


def _is_instance_generic_alias_tuple(
    obj: Any,  # noqa: ANN401
    args: tuple[Any, ...],
) -> bool:
    if len(args) == 1:
        argstype = (args[0], ...)
    argstype = args

    if argstype[-1] is Ellipsis:
        argtype = args[0]
        argtype: type | GenericAlias | UnionType | None
        return all(is_instance(item, argtype) for item in obj)
    for i, argtype in enumerate(args):
        if i >= len(obj):
            break
        if not is_instance(obj[i], argtype):
            return False
    return True


def _is_instance_generic_alias(  # pylint: disable=R0911  # noqa: PLR0911
    obj: Any,  # noqa: ANN401
    objtype: GenericAlias,
) -> bool:
    orig = get_origin(objtype)
    # get_origin will return None, but type checker thinks it
    # returns a type always.
    if orig is None:  # type: ignore[arg-type]
        msg = "Invalid generic type"
        raise TypeError(msg)

    if not rubisco_isinstance(obj, orig):
        return False

    args = get_args(objtype)
    if not args:
        return True

    if orig in (list, set):
        argtype = args[0]
        argtype: type | GenericAlias | UnionType | None
        return all(is_instance(item, argtype) for item in obj)
    if orig is dict:
        return _is_instance_generic_alias_dict(obj, args)
    if orig is tuple:
        return _is_instance_generic_alias_tuple(obj, args)
    if orig is EllipsisType:
        # Ellipsis is a valid type for all objects.
        return True

    warnings.warn(
        f"Unsupported generic type: {orig}",
        RuntimeWarning,
        stacklevel=2,
    )
    return rubisco_isinstance(obj, orig)


def is_instance(
    obj: Any,  # noqa: ANN401
    objtype: type | GenericAlias | UnionType | None,
) -> bool:
    """Check if an object is an instance of a type or a union of types.

    If objtype is None, return True if obj is None.

    Args:
        obj (Any): Object to check.
        objtype (type | GenericAlias | UnionType | None): Type or union of types
            to check against.

    """
    if objtype is None:
        return obj is None

    if get_origin(objtype) is UnionType:
        return any(is_instance(obj, t) for t in get_args(objtype))

    if rubisco_isinstance(objtype, GenericAlias):
        ot = cast("GenericAlias", objtype)
        return _is_instance_generic_alias(obj, ot)

    return rubisco_isinstance(obj, cast("type", objtype))


@beartype
def type_assert[AT](instance: AT, valtype: ValType[AT]) -> AT:
    """Assert the type of the instance.

    Args:
        instance (AT): The instance to check.
        valtype (ValType[AT]): The expected type.

    Raises:
        RUTypeError: If the instance is not of the expected type.

    Returns:
        AT: The instance.

    """
    if not is_instance(instance, valtype):
        valtype_name = getattr(valtype, "__name__", repr(valtype))
        raise RUTypeError(
            fast_format_str(
                _(
                    "The value needs to be ${{type}}"
                    " instead of ${{value_type}}.",
                ),
                fmt={
                    "type": valtype_name,
                    "value_type": repr(type(instance).__name__),
                },
            ),
        )

    return instance


@beartype
def get_list_check[LT](
    instance: list[LT],
    idx: int,
    valtype: ValType[LT],
) -> LT:
    """Get the item at the index and check its type.

    Args:
        instance (list[LT]): The list to get the item from.
        idx (int): The index of the item.
        valtype (ValType[LT]): The type of the item.

    Raises:
        IndexError: If the index is out of range.
        RUTypeError: If the item is not of the type.

    Returns:
        T: The item at the index.

    """
    val = instance[idx]
    type_assert(val, valtype)

    return val


@beartype
def get_dict_check[KT, VT](
    instance: dict[KT, VT],
    key: KT,
    valtype: ValType[VT],
    default: VT | EllipsisType = ...,
) -> VT:
    """Get the value of the key and check its type.

    Args:
        instance (dict[KT, VT]): The dict to get the value from.
        key (KT): The key of the value.
        valtype (ValType[VT]): The type of the value.
        default (VT, optional): The default value. Defaults to Ellipsis.

    Returns:
        VT: The value of the key.

    """
    val = instance[key] if default is ... else instance.get(key, default)

    type_assert(val, valtype)

    return val
