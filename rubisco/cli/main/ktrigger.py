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

"""The CLI kernel trigger."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, cast

import colorama
import rich
import rich.live
import rich.progress
from pygments import highlight  # type: ignore[attr-defined]
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
from rich.tree import Tree

from rubisco.cli.input import ask_yesno
from rubisco.cli.main.project_config import get_hooks
from rubisco.cli.osc9 import ProgressBarState, conemu_progress
from rubisco.cli.output import (
    get_prompt,
    output_error,
    output_hint,
    output_line,
    output_step,
    output_warning,
    pop_level,
    push_level,
    sum_level_indent,
)
from rubisco.config import (
    DEFAULT_CHARSET,
)
from rubisco.kernel.config_file import config_file
from rubisco.lib.l10n import _, locale_language, locale_language_name
from rubisco.lib.log import logger
from rubisco.lib.speedtest import C_INTMAX
from rubisco.lib.tree import Tree as RUTree
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import (
    IKernelTrigger,
)

if TYPE_CHECKING:
    from pathlib import Path

    from rubisco.envutils.env import RUEnvironment
    from rubisco.envutils.packages import ExtensionPackageInfo
    from rubisco.kernel.project_config.project_config import ProjectConfigration
    from rubisco.kernel.workflow.step import Step
    from rubisco.kernel.workflow.workflow import Workflow
    from rubisco.lib.process import Process
    from rubisco.lib.version import Version
    from rubisco.shared.extension import IRUExtension


# ruff: noqa: D102 D107
# pylint: disable=missing-function-docstring

__all__ = ["RubiscoKTrigger"]


class CurrentProgressColumn(rich.progress.ProgressColumn):
    """Progress bar column for infinite progres bar."""

    def render(self, task: rich.progress.Task) -> str:
        """Render for CurrentProgressColumn.

        Args:
            task (Task): The progress task

        Returns:
            Status message.

        """
        if task.total:
            conemu_progress(ProgressBarState.NORMAL, task.completed, task.total)
        else:
            conemu_progress(ProgressBarState.WAITING)
        status = task.fields.get("status", "")
        return f"[cyan]{status}[/cyan]" if status else ""


class RubiscoKTrigger(  # pylint: disable=too-many-public-methods
    IKernelTrigger,
):  # Rubisco CLI kernel trigger.
    """Rubisco kernel trigger."""

    # Singleton pattern, but linter does not like it.
    cur_progress: rich.progress.Progress | None
    tasks: dict[str, rich.progress.TaskID]
    task_types: dict[str, str]
    live: rich.live.Live | None
    _speedtest_hosts: dict[str, str]
    _rich_printer: object

    def __init__(self) -> None:
        super().__init__()
        self.cur_progress = None
        self.tasks = {}
        self.task_types = {}
        self.live = None
        self._speedtest_hosts = {}
        self._rich_printer = rich.print

    def _highlight_command(self, shell: Path, cmd: str) -> str:
        shellname = shell.name.lower()
        if shellname in {"sh", "ksh", "csh", "bash", "fish", "zsh"}:
            return highlight(
                cmd,
                get_lexer_by_name(shellname),
                Terminal256Formatter(),
            )
        return cmd

    def pre_exec_process(self, *, proc: Process) -> None:
        output_step(
            fast_format_str(
                _("Executing: [cyan]${{cmd}}[/cyan] ..."),
                fmt={"cmd": proc.origin_cmd.strip()},
            ),
        )
        sys.stdout.write(colorama.Fore.LIGHTBLACK_EX)
        sys.stdout.flush()

    def post_exec_process(
        self,
        *,
        proc: Process,  # noqa: ARG002
        retcode: int,  # noqa: ARG002
        raise_exc: bool,  # noqa: ARG002
    ) -> None:
        sys.stdout.write(colorama.Fore.RESET)
        sys.stdout.flush()

    def file_exists(self, *, path: Path) -> None:
        if not ask_yesno(
            fast_format_str(
                _(
                    "${{path}} already exists. [yellow]Overwrite[/yellow]?",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
            default=True,
        ):
            raise KeyboardInterrupt

    def on_new_task(
        self,
        *,
        task_start_msg: str,
        task_name: str,
        total: float | None,
    ) -> None:
        output_step(task_start_msg)

        if self.cur_progress is None:
            self.cur_progress = rich.progress.Progress(
                rich.progress.TextColumn(
                    "[progress.description]{task.description}",
                ),
                rich.progress.BarColumn(),
                CurrentProgressColumn(),
                rich.progress.TaskProgressColumn(),
                rich.progress.TimeElapsedColumn(),
                rich.progress.TimeRemainingColumn(),
                rich.progress.MofNCompleteColumn(),
            )
            self.cur_progress.start()
        if task_name in self.tasks:
            self.cur_progress.update(self.tasks[task_name], completed=0)
        task_id = self.cur_progress.add_task(
            task_name,
            total=None if total == -1 else total,
        )
        self.tasks[task_name] = task_id

        def _print_wrapper(
            *args: list[Any],
            flush: bool = False,
            **kwargs: dict[str, Any],
        ) -> None:
            if not self.cur_progress:
                self._rich_printer(*args, **kwargs, flush=flush)  # type: ignore[arg-type]
                return

            self.cur_progress.print(*args, **kwargs)  # type: ignore[arg-type]
            if flush:
                sys.stdout.buffer.flush()

        rich.print = _print_wrapper  # Evil hacking.

    def on_progress(  # pylint: disable=R0913
        self,
        *,
        task_name: str,
        current: float,
        delta: bool = False,
        update_msg: str = "",
        status_msg: str = "",
    ) -> None:
        output_line(update_msg)

        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
        if delta:
            self.cur_progress.update(
                self.tasks[task_name],
                advance=current,
                status=status_msg,
            )
        else:
            self.cur_progress.update(
                self.tasks[task_name],
                completed=current,
                status=status_msg,
            )

    def set_progress_total(self, *, task_name: str, total: float) -> None:
        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
        self.cur_progress.update(self.tasks[task_name], total=total)

    def on_finish_task(self, *, task_name: str) -> None:
        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
        self.cur_progress.remove_task(self.tasks[task_name])
        del self.tasks[task_name]
        if not self.tasks:
            self.cur_progress.stop()
            self.cur_progress = None
            if self._rich_printer:
                rich.print = self._rich_printer

    def on_syspkg_installation_skip(
        self,
        *,
        packages: list[str],
        message: str,
    ) -> None:
        output_warning(message)
        output_hint(
            fast_format_str(
                _(
                    "Please install the following packages manually:"
                    " [bold]${{packages}}[/bold].",
                ),
                fmt={"packages": ", ".join(packages)},
            ),
        )

        if not ask_yesno(_("Continue anyway?"), default=False):
            raise KeyboardInterrupt

    def on_update_git_repo(self, *, path: Path, branch: str) -> None:
        output_step(
            fast_format_str(
                _(
                    "Updating Git repository ${{path}}(${{branch}}) ...",
                ),
                fmt={"path": make_pretty(path), "branch": make_pretty(branch)},
            ),
        )

    def on_clone_git_repo(
        self,
        *,
        url: str,
        path: Path,
        branch: str,
    ) -> None:
        output_step(
            fast_format_str(
                _(
                    "Cloning Git repository ${{url}} (${{branch}}) into "
                    "${{path}} ...",
                ),
                fmt={"url": url, "branch": branch, "path": make_pretty(path)},
            ),
        )

    def on_hint(self, *, message: str) -> None:
        output_hint(message)

    def on_warning(self, *, message: str) -> None:
        output_warning(message)

    def on_error(self, *, message: str) -> None:
        output_error(message)

    def _update_live(self) -> None:
        if self.live is None:
            msg = "RubiscoKTrigger.live is None."
            raise ValueError(msg)
        msg = ""
        for host_, status in self._speedtest_hosts.items():
            msg += (
                sum_level_indent(-2)
                + get_prompt(-2, ">", ">")
                + " "
                + fast_format_str(
                    _("Testing ${{host}} ... ${{status}}"),
                    fmt={"host": host_, "status": status},
                )
                + "\n"
            )
        self.live.update(msg)

    def pre_speedtest(self, *, host: str) -> None:
        conemu_progress(ProgressBarState.WAITING)
        if self.live is None:
            output_step(_("Performing websites speed test ..."))
            self.live = rich.live.Live()
            self.live.start()
            self._speedtest_hosts.clear()
        self._speedtest_hosts[host] = _("[yellow]Testing[/yellow] ...")
        self._update_live()

    def post_speedtest(self, *, host: str, speed: int) -> None:
        if self.live is None:
            msg = "RubiscoKTrigger.live is None."
            raise ValueError(msg)
        if speed == -1:
            self._speedtest_hosts[host] = _("[red]Canceled[/red]")
        elif speed == C_INTMAX:
            self._speedtest_hosts[host] = _("[red]Failed[/red]")
        else:
            self._speedtest_hosts[host] = fast_format_str(
                _("${{speed}} us"),
                fmt={"speed": str(speed)},
            )

        self._update_live()

        cant_stop = False
        for status in self._speedtest_hosts.values():
            cant_stop |= status == _(
                "[yellow]Testing[/yellow] ...",
            )

        if not cant_stop:
            self.live.stop()
            self.live = None

    def stop_speedtest(self, *, choise: str | None) -> None:
        conemu_progress(ProgressBarState.NORMAL)
        if self.live is None:
            return
        self.live.stop()
        self.live = None
        if choise:
            output_step(
                fast_format_str(
                    _("Selected mirror: ${{url}}"),
                    fmt={"url": choise},
                ),
            )

    def pre_run_workflow_step(self, *, step: Step) -> None:
        if step.name.strip():
            output_step(
                fast_format_str(
                    _(  # Don't remove next line's comment.
                        "Running: [white]${{name}}[/white]"  # Black?
                        " [black](${{id}})[/black]",
                    ),
                    fmt={"name": step.name, "id": step.id},
                ),
            )
            push_level()

    def post_run_workflow_step(self, *, step: Step) -> None:
        if step.name.strip():
            pop_level()

    def pre_run_workflow(self, *, workflow: Workflow) -> None:
        if workflow.name:
            output_step(
                fast_format_str(
                    _(
                        "Running workflow: [white]${{name}}[/white] "
                        "[black](${{id}})[/black]",
                    ),
                    fmt={"name": workflow.name, "id": workflow.id},
                ),
            )
            push_level()

    def post_run_workflow(self, *, workflow: Workflow) -> None:
        if workflow.name:
            pop_level()
            output_step(
                fast_format_str(
                    _("Workflow '${{name}}' finished."),
                    fmt={"name": workflow.name},
                ),
            )

    def pre_run_matrix(self, *, variables: dict[str, object]) -> None:
        if not config_file.config.get("verbose", False):
            output_step(_("Running matrix jobs ..."))
            push_level()
            return

        output_step(fast_format_str(_("Running jobs with variables:")))
        push_level()
        for key, val in variables.items():
            output_line(f"{key}: {val!r}")

    def post_run_matrix(
        self,
        *,
        variables: dict[str, object],  # noqa: ARG002
    ) -> None:
        pop_level()

    def on_mkdir(self, *, path: Path) -> None:
        output_step(
            fast_format_str(
                _("Creating directory: ${{path}} ..."),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    def _convert_tree(self, tree: RUTree[object], rich_tree_root: Tree) -> None:
        """Convert RUTree to rich Tree."""
        for ru_node in tree.children:
            node = rich_tree_root.add(str(ru_node.value))
            if ru_node.children:
                self._convert_tree(ru_node, node)

    def _output_tree(self, tree: RUTree[object]) -> None:
        """Output RUTree as rich Tree."""
        rich_tree = Tree(str(tree.value))
        self._convert_tree(tree, rich_tree)
        rich.print(rich_tree)

    def on_output(self, *, message: object, raw: bool = True) -> None:
        if raw:
            if isinstance(message, RUTree):
                self._output_tree(cast("RUTree[object]", message))
            else:
                rich.print(str(message))
        else:
            output_line(message if isinstance(message, str) else repr(message))

    def on_move_file(self, *, src: Path, dst: Path) -> None:
        output_step(
            fast_format_str(
                _("Moving file ${{src}} to ${{dst}} ..."),
                fmt={
                    "src": make_pretty(src.absolute()),
                    "dst": make_pretty(dst.absolute()),
                },
            ),
        )

    def on_copy(self, *, src: Path, dst: Path) -> None:
        output_step(
            fast_format_str(
                _("Copying ${{src}} to ${{dst}} ..."),
                fmt={
                    "src": make_pretty(src.absolute()),
                    "dst": str(dst.absolute()),
                },
            ),
        )

    def on_remove(self, *, path: Path) -> None:
        output_step(
            fast_format_str(
                _("Removing ${{path}} ..."),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    def on_file_selected(self, *, path: Path) -> None:
        if not config_file.config.get("verbose", False):
            return

        output_step(
            fast_format_str(
                _("Selected: ${{path}}"),
                fmt={"path": make_pretty(path)},
            ),
        )

    def on_extension_loaded(
        self,
        *,
        instance: IRUExtension,  # noqa: ARG002
        ext_info: ExtensionPackageInfo,
    ) -> None:
        if not config_file.config.get("verbose", False):
            return

        output_step(
            fast_format_str(
                _("Extension '${{name}}' loaded."),
                fmt={"name": ext_info.name},
            ),
        )

    def on_show_project_info(self, *, project: ProjectConfigration) -> None:
        rich.print(
            fast_format_str(
                _(
                    "[dark_orange]Rubisco CLI Language:[/dark_orange] "
                    "'${{locale}}' '${{charset}}' '${{language_name}}'",
                ),
                fmt={
                    "locale": locale_language(),
                    "charset": DEFAULT_CHARSET,
                    "language_name": locale_language_name(),
                },
            ),
        )
        rich.print(
            fast_format_str(
                _("[dark_orange]Project:[/dark_orange] ${{name}}"),
                fmt={"name": make_pretty(project.name)},
            ),
        )
        rich.print(
            fast_format_str(
                _("[dark_orange]Configuration:[/dark_orange] ${{path}}"),
                fmt={"path": make_pretty(project.config.path)},
            ),
        )
        rich.print(
            fast_format_str(
                _(
                    "[dark_orange]Version:[/dark_orange]"
                    " v[white]${{version}}[/white]",
                ),
                fmt={"version": str(project.version)},
            ),
        )

        if isinstance(project.maintainers, list):
            maintainers = "\n  ".join([str(m) for m in project.maintainers])
        else:
            maintainers = str(project.maintainers)
        rich.print(
            fast_format_str(
                _("[dark_orange]Maintainers:[/dark_orange] ${{maintainers}}"),
                fmt={"maintainers": maintainers},
            ),
        )
        _u = _("[yellow]Unknown[/yellow]")
        rich.print(
            fast_format_str(
                _("[dark_orange]License:[/dark_orange] ${{license}}"),
                fmt={"license": project.license or _u},
            ),
        )
        rich.print(
            fast_format_str(
                _("[dark_orange]Description:[/dark_orange] ${{desc}}"),
                fmt={"desc": project.description},
            ),
        )

        rich.print(_("[dark_orange]Hooks:[/dark_orange]"))

        for hook_name in project.hooks:  # Bind all hooks.
            hook_text = fast_format_str(
                "\t[cyan]${{name}}[/cyan]",
                fmt={"name": hook_name},
            )
            num_text = fast_format_str(
                _("(${{num}} hooks)"),
                fmt={"num": str(len(get_hooks()[hook_name]))},
            )
            formatted_str = f"{hook_text:<60}\t{num_text:<10}"
            rich.print(formatted_str)

    def on_mklink(
        self,
        *,
        src: Path,
        dst: Path,
        symlink: bool,
    ) -> None:
        if symlink:
            output_step(
                fast_format_str(
                    _(
                        "Creating symbolic link: ${{src}} -> ${{dst}} ...",
                    ),
                    fmt={
                        "src": make_pretty(src.absolute()),
                        "dst": make_pretty(dst),
                    },
                ),
            )
        else:
            output_step(
                fast_format_str(
                    _(
                        "Creating hard link: ${{src}} -> ${{dst}} ...",
                    ),
                    fmt={
                        "src": make_pretty(src.absolute()),
                        "dst": make_pretty(dst),
                    },
                ),
            )

    def on_create_venv(self, *, path: Path) -> None:
        output_step(
            fast_format_str(
                _(
                    "Creating Rubisco extension environment: ${{path}} ...",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    def on_install_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        if dest.is_global():
            dest_msg = _("global")
        elif dest.is_user():
            dest_msg = _("user")
        else:
            dest_msg = _("workspace")
        output_step(
            fast_format_str(
                _(
                    "Installing extension [green]${{name}}[/green]:[cyan]"
                    "${{version}}[/cyan] to [yellow]${{dest}}[/yellow]"
                    " (${{path}}) ...",
                ),
                fmt={
                    "name": ext_name,
                    "version": str(ext_version),
                    "path": make_pretty(dest.path),
                    "dest": dest_msg,
                },
            ),
        )
        push_level()

    def on_extension_installed(
        self,
        *,
        dest: RUEnvironment,  # noqa: ARG002
        ext_name: str,
        ext_version: Version,
    ) -> None:
        pop_level()
        output_step(
            fast_format_str(
                _(
                    "Extension [green]${{name}}[/green]:[cyan]${{version}}"
                    "[/cyan] was successfully installed.",
                ),
                fmt={"name": ext_name, "version": str(ext_version)},
            ),
        )

    def on_uninstall_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        if dest.is_global():
            dest_msg = _("global")
        elif dest.is_user():
            dest_msg = _("user")
        else:
            dest_msg = _("workspace")
        output_step(
            fast_format_str(
                _(
                    "Uninstalling extension [green]${{name}}[/green]:"
                    "[cyan]${{version}}[/cyan] from [yellow]"
                    "${{dest}}[/yellow] (${{path}}) ...",
                ),
                fmt={
                    "name": ext_name,
                    "version": str(ext_version),
                    "path": make_pretty(dest.path),
                    "dest": dest_msg,
                },
            ),
        )
        push_level()

    def on_extension_uninstalled(
        self,
        *,
        dest: RUEnvironment,  # noqa: ARG002 # pylint: disable=unused-argument
        ext_name: str,
        ext_version: Version,
    ) -> None:
        pop_level()
        output_step(
            fast_format_str(
                _(
                    "Extension [green]${{name}}[/green]:[cyan]${{version}}"
                    "[/cyan] was successfully uninstalled.",
                ),
                fmt={"name": ext_name, "version": str(ext_version)},
            ),
        )

    def on_upgrade_extension(
        self,
        *,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        if dest.is_global():
            dest_msg = _("global")
        elif dest.is_user():
            dest_msg = _("user")
        else:
            dest_msg = _("workspace")
        output_step(
            fast_format_str(
                _(
                    "Upgrading extension [green]${{name}}[/green]:"
                    "[cyan]${{version}}[/cyan] from [yellow]"
                    "${{dest}}[/yellow] (${{path}}) ...",
                ),
                fmt={
                    "name": ext_name,
                    "version": str(ext_version),
                    "path": make_pretty(dest.path),
                    "dest": dest_msg,
                },
            ),
        )
        push_level()

    def on_extension_upgraded(
        self,
        *,
        dest: RUEnvironment,  # noqa: ARG002 # pylint: disable=unused-argument
        ext_name: str,
        ext_version: Version,
    ) -> None:
        pop_level()
        output_step(
            fast_format_str(
                _(
                    "Extension [green]${{name}}[/green]:[cyan]${{version}}"
                    "[/cyan] was successfully upgraded.",
                ),
                fmt={"name": ext_name, "version": str(ext_version)},
            ),
        )

    def on_verify_uninstall_extension(
        self,
        *,
        dest: RUEnvironment,
        query: set[ExtensionPackageInfo],
    ) -> None:
        if dest.is_global():
            dest_msg = _("global")
        elif dest.is_user():
            dest_msg = _("user")
        else:
            dest_msg = _("workspace")
        msg = fast_format_str(
            _(
                "The following extensions will be uninstalled from [yellow]"
                "${{dest}}[/yellow] (${{path}}):",
            ),
            fmt={"path": make_pretty(dest.path), "dest": dest_msg},
        )

        rich.print(msg)
        for ext in query:
            rich.print(
                fast_format_str(
                    "\t[green]${{name}}[/green]:[cyan]${{version}}[/cyan]",
                    fmt={"name": ext.name, "version": str(ext.version)},
                ),
            )

        if not ask_yesno(
            _("Continue?"),
            default=True,
        ):
            raise KeyboardInterrupt

    def on_wait(self, *, msg: str, cur_time: int) -> None:
        """Update waiting message.

        Args:
            msg (str): Waiting message.
            cur_time (int): Current time.

        Raises:
            RUValueError: Waiting message is empty.

        """
        conemu_progress(ProgressBarState.WAITING)
        rich.print(
            fast_format_str(
                msg,
                fmt={"seonds": cur_time},
            ),
            end="\r",
        )

    def end_wait(
        self,
        *,
        msg: str,  # noqa: ARG002
    ) -> None:
        """End for waiting.

        Args:
            msg (str): The wait message.

        """
        conemu_progress(ProgressBarState.DEFAULT)

    def on_step(self, *, msg: str) -> None:
        """Update step message.

        Args:
            msg (str): Step message.

        """
        output_step(msg)

    def on_steptask_start(self, *, msg: str) -> None:
        """On step task started.

        Args:
            msg (str): Step message.

        """
        output_step(msg)
        push_level()

    def on_steptask_end(
        self,
        *,
        msg: str,  # noqa: ARG002
    ) -> None:
        """On step task ended.

        Args:
            msg (str): Step message.

        """
        pop_level()

    def on_chdir(self, *, path: Path) -> None:
        """On change working directory.

        Args:
            path (Path): New working directory.

        """
        output_step(
            fast_format_str(
                _("Entering directory ${{path}} ..."),
                fmt={"path": make_pretty(path)},
            ),
        )

    def on_leaving_dir(self, *, path: Path) -> None:
        """On leaving working directory.

        Args:
            path (Path): New working directory.

        """
        output_step(
            fast_format_str(
                _("Leaving directory ${{path}} ..."),
                fmt={"path": make_pretty(path)},
            ),
        )
