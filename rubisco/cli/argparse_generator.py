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

"""Generate argparser from CommandEventFS."""

from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, cast

from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.lib.convert import convert_to
from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.l10n import _
from rubisco.lib.typecheck import is_instance

if TYPE_CHECKING:
    from argparse import _SubParsersAction  # type: ignore[attr-defined]

type SubParser = "_SubParsersAction[ArgumentParser]"  # type: ignore[valid-type] # pylint: disable=line-too-long

_subparsers: dict[str, SubParser] = {}


def _get_subparser(
    path: EventPath,
    parent: ArgumentParser,
) -> SubParser:
    name = path.parent.normpath().as_posix()
    val = _subparsers.get(name)
    if val:
        return val
    subparser = parent.add_subparsers(
        metavar="",
        required=True,
    )
    _subparsers[name] = subparser
    return subparser


def _fill_options(
    path: EventPath,
    args: Namespace,
) -> None:
    for option in path.stat().options:
        if not hasattr(args, option.name) and option.default is None:
            msg = f"Option {option.name} is not provided in the namespace."
            raise ValueError(msg)
        val = getattr(args, option.name, None)
        val = val if val is not None else option.default
        val = convert_to(val, option.typecheck)
        path.set_option(option.name, val)

    if path.normpath().as_posix() != "/":
        _fill_options(path.parent, args)


def _fill_arguments(
    data: EventFileData,
    args: Namespace,
) -> list[str]:
    args_list: list[str] = []

    if isinstance(data.args, list):
        for arg in data.args:
            if not hasattr(args, arg.name):
                msg = f"Argument {arg.name} is not provided in the namespace."
                raise ValueError(msg)
            args_list.append(getattr(args, arg.name))
    else:
        if not hasattr(args, data.args.name):
            msg = f"Argument {data.args.name} is not provided in the namespace."
            raise ValueError(msg)
        args_list.extend(getattr(args, data.args.name))

    return args_list


def _call_event(path: EventPath, args: Namespace) -> None:
    """Call event function.

    Args:
        path (EventPath): The event path.
        args (Namespace): The namespace.

    """
    data = path.read()
    if not data:
        msg = f"Not a file, this should never happen: {path}"
        raise ValueError(msg)

    _fill_options(path, args)
    path.execute(_fill_arguments(data, args))


def _gen_options(event_path: EventPath, parser: ArgumentParser) -> None:
    for options in event_path.stat().options:
        names: list[str] = []
        for name in [options.name, *options.aliases]:
            names.append(f"--{name}" if len(name) > 1 else f"-{name}")  # noqa: PERF401
        parser.add_argument(
            *names,
            type=options.typecheck if options.typecheck is list else str,
            help=options.description,
            action="store",
            dest=options.name,
            default=options.default,
            nargs="?" if options.default else None,
        )

        advanced_opts = options.ext_attributes.get("cli-advanced-options", [])
        if not is_instance(
            advanced_opts,
            list[dict[str, list[str] | int | str | None]],
        ):
            raise RUTypeError(
                _("The advanced options must be a list."),
                hint=_(
                    "Advanced options must be a list of "
                    "`dict[str, list[str] | int | str | None]`.",
                ),
            )

        for ext_args in cast(
            "list[dict[str, int | str | None]]",
            advanced_opts,
        ):
            ext_names_ = ext_args.pop("name", None)
            if is_instance(ext_names_, str):
                ext_names = [cast("str", ext_names_)]
            else:
                ext_names = cast("list[str]", ext_names_)
            parser.add_argument(
                *ext_names,
                dest=options.name,
                **ext_args,  # type: ignore[arg-type]
            )


def _gen_args(
    event_path: EventPath,
    parser: ArgumentParser,
) -> None:
    data = event_path.read()
    if not data:
        msg = f"Not a file, this should never happen: {event_path}"
        raise ValueError(msg)
    if isinstance(data.args, list):
        for arg in data.args:
            parser.add_argument(
                arg.name,
                type=arg.typecheck,
                help=arg.description,
                action="store",
                default=arg.default,
            )
    else:
        parser.add_argument(
            data.args.name,
            help=data.args.description,
            action="store",
            nargs="*" if data.args.mincount == 0 else "+",
        )


def _gen_from_file(event_path: EventPath, parent: ArgumentParser) -> None:
    data = event_path.read()
    if not data:
        msg = f"Not a file, this should never happen: {event_path}"
        raise ValueError(msg)

    subparser = _get_subparser(event_path, parent)
    parser = subparser.add_parser(
        event_path.name,
        help=event_path.stat().description,
        formatter_class=RUHelpFormatter,
        allow_abbrev=True,
    )

    def _callback(args: Namespace) -> None:
        _call_event(event_path, args)

    parser.set_defaults(callback=_callback)
    _gen_options(event_path, parser)
    _gen_args(event_path, parser)


def _gen_from_dir(event_path: EventPath, parent: ArgumentParser) -> None:
    subparser = _get_subparser(event_path, parent)
    if event_path == "/":
        parser = parent
    else:
        parser = subparser.add_parser(
            event_path.name,
            help=event_path.stat().description,
            formatter_class=RUHelpFormatter,
            allow_abbrev=True,
        )
    _gen_options(event_path, parser)
    for subdir in event_path.list_dirs():
        _gen_from_dir(subdir, parser)
    for file in event_path.list_files():
        _gen_from_file(file, parser)
    for link in event_path.list_aliases():
        _gen_from_link(link, parent)


def _gen_from_link(event_path: EventPath, parent: ArgumentParser) -> None:
    if not event_path.stat().alias_to or not event_path.is_alias():
        msg = f"Not a link: {event_path}, this should never happen."
        raise ValueError(msg)
    if event_path.is_dir():
        _gen_from_dir(event_path, parent)
    elif event_path.is_file():
        _gen_from_file(event_path, parent)
    elif event_path.is_mount_point():
        pass  # Mount point will be mounted later.
    else:
        msg = f"Unknown event type: {event_path}, this should never happen."
        raise ValueError(msg)


def gen_argparse(
    event_path: EventPath,
    parent: ArgumentParser,
) -> None:
    """Generate argparser from CommandEventFS.

    Args:
        event_path (EventPath): The event path.
        parent (ArgumentParser): The parent argument parser.

    """
    _gen_from_dir(event_path, parent)
