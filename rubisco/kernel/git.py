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

"""Mirrorlist for extension installer."""

from pathlib import Path

from git.exc import GitError
from git.remote import Remote
from git.repo import Repo
from git.util import RemoteProgress

from rubisco.kernel.mirrorlist import get_url
from rubisco.lib.exceptions import RUError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.process import Process
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, OutputMethod, call_ktrigger

__all__ = [
    "git_branch_set_upstream",
    "git_clone",
    "git_get_remote",
    "git_has_remote",
    "git_set_remote",
    "git_update",
    "is_git_repo",
]


def _gitpython_progress_update_opname(  # noqa: PLR0911 # pylint: disable=R0911
    op_code: int,
) -> str:
    if op_code & RemoteProgress.CHECKING_OUT:
        return _("Checking out files")
    if op_code & RemoteProgress.COMPRESSING:
        return _("Compressing objects")
    if op_code & RemoteProgress.COUNTING:
        return _("Counting objects")
    if op_code & RemoteProgress.FINDING_SOURCES:
        return _("Finding sources")
    if op_code & RemoteProgress.RECEIVING:
        return _("Receiving objects")
    if op_code & RemoteProgress.RESOLVING:
        return _("Resolving deltas")
    if op_code & RemoteProgress.WRITING:
        return _("Writing objects")
    return "???"


def _gitpython_progress_update(
    op_code: int,
    cur_count: str | float,
    max_count: str | float | None,
    message: str,  # noqa: ARG001 # pylint: disable=W0613
) -> None:
    if isinstance(cur_count, str) or isinstance(max_count, str):
        return

    msg = _gitpython_progress_update_opname(op_code)

    if op_code & RemoteProgress.BEGIN:
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_start_msg="",
            task_name=msg,
            total=max_count,
        )
    elif op_code & RemoteProgress.END:
        percent = f"{int(cur_count)}/{int(max_count)}" if max_count else ""
        finish_msg = f"{msg}: {percent}"
        call_ktrigger(
            IKernelTrigger.on_output,
            message=finish_msg,
            method=OutputMethod.RAW,
        )
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=msg)
    else:
        call_ktrigger(
            IKernelTrigger.on_progress,
            task_name=msg,
            current=cur_count,
            delta=False,
        )


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path (Path): Path to the directory.

    Returns:
        bool: True if the directory is a git repository.

    """
    if not path.is_dir():
        return False

    try:
        Repo(path).close()
    except GitError:
        return False
    return True


def git_update(
    path: Path,
    branch: str = "main",
    *,
    protocol: str = "http",
    use_fastest: bool = True,
) -> None:
    """Update a git repository.

    Args:
        path (Path): Path to the repository.
        branch (str, optional): Branch to update. Defaults to "main".
        protocol (str, optional): Protocol to use. Defaults to "http".
        use_fastest (bool, optional): Use the fastest mirror. Defaults to True.

    """
    if not path.exists():
        logger.error("Repository '%s' does not exist.", str(path))
        raise FileNotFoundError(
            fast_format_str(
                _(
                    "Repository ${{path}} not found.",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    logger.info("Updating repository '%s'...", str(path))
    call_ktrigger(IKernelTrigger.on_update_git_repo, path=path, branch=branch)
    if not is_git_repo(path):
        logger.error("Repository '%s' is not a git repository.", str(path))
        raise RUError(
            fast_format_str(
                _("Repository ${{path}} is not a git repository."),
                fmt={"path": str(path)},
            ),
        )
    try:
        repo = Repo(path)
        if "rubisco-url" in [remote.name for remote in repo.remotes]:
            rubisco_url = Remote(repo, "rubisco-url")
            mirror_url = get_url(
                rubisco_url.url,
                protocol=protocol,
                use_fastest=use_fastest,
            )
            if not Remote(repo, "mirror").exists():
                repo.create_remote("mirror", mirror_url)
            else:
                repo.remote("mirror").set_url(mirror_url)
            mirror = repo.remote("mirror")
            mirror.pull(branch)
            # Set upstream to origin.
            repo.branches[branch].set_tracking_branch(
                repo.remotes.origin.refs[branch],
            )
        else:
            origin = repo.remote("origin")
            origin.pull()
    except GitError as exc:
        logger.error("Git operation failed: %s", str(exc))
        raise RUError(
            fast_format_str(
                _("Git operation failed: ${{exc}}"),
                fmt={"exc": str(exc)},
            ),
        ) from exc
    logger.info("Repository '%s' updated.", str(path))


def git_clone(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    url: str,
    path: Path,
    branch: str = "main",
    protocol: str = "http",
    *,
    shallow: bool = True,
    strict: bool = False,
    use_fastest: bool = True,
) -> None:
    """Clone a git repository.

    Args:
        url (str): Repository URL.
        path (Path): Path to clone the repository.
        branch (str, optional): Branch to clone. Defaults to "main".
        protocol (str, optional): Protocol to use. Defaults to "http".
        shallow (bool, optional): Shallow clone. Defaults to True.
        strict (bool, optional): Raise an error if the repository already
            exists. If False, the repository will be updated. Defaults to
            False.
        use_fastest (bool, optional): Use the fastest mirror. Defaults to True.

    """
    if is_git_repo(path):
        if strict:
            logger.error("Repository already exists.")
            raise FileExistsError(
                fast_format_str(
                    _(
                        "Repository ${{path}} already exists.",
                    ),
                    fmt={"path": str(path)},
                ),
            )
        logger.warning("Repository already exists, Updating...")
        git_update(path, branch, protocol=protocol, use_fastest=use_fastest)
        return

    old_url = url
    url = get_url(url, protocol=protocol, use_fastest=use_fastest)

    logger.info("Cloning repository '%s' to '%s'...", url, str(path))
    call_ktrigger(
        IKernelTrigger.on_clone_git_repo,
        url=url,
        path=path,
        branch=branch,
    )
    try:
        repo = Repo.clone_from(
            url,
            path,
            branch=branch,
            progress=_gitpython_progress_update,
            multi_options=["--depth=1"] if shallow else [],
        )
    except GitError as exc:
        logger.error("Repository '%s' clone failed.", str(path))
        raise RUError(
            fast_format_str(
                _("Git operation failed: ${{exc}}"),
                fmt={"exc": str(exc)},
            ),
        ) from exc
    logger.info("Repository '%s' cloned.", str(path))

    if old_url != url:  # Reset the origin URL to official.
        origin_url = get_url(old_url, protocol=protocol, use_fastest=False)
        repo.remote("origin").set_url(origin_url)
        repo.create_remote("rubisco-url", old_url)
        repo.create_remote("mirror", url)
        # Set the upstream branch.
        repo.branches[branch].set_tracking_branch(
            repo.remotes.origin.refs[branch],
        )


def git_has_remote(path: Path, remote: str) -> bool:
    """Check if a remote repository exists.

    Args:
        path (Path): Path to the repository.
        remote (str, optional): Remote name.

    Returns:
        bool: True if the remote repository exists.

    """
    _stdout, _stderr, retcode = Process(
        ["git", "remote", "get-url", remote],
        cwd=path,
    ).popen(
        stdout=False,
        stderr=0,
        fail_on_error=False,
    )
    return retcode == 0


def git_get_remote(path: Path, remote: str = "origin") -> str:
    """Get the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str, optional): Remote name. Defaults to "origin".

    Returns:
        str: Remote URL.

    """
    return Process(["git", "remote", "get-url", remote], cwd=path).popen(
        stderr=False,
    )[0]


def git_set_remote(path: Path, remote: str, url: str) -> None:
    """Set the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str): Remote name.
        url (str): Remote URL.

    """
    if git_has_remote(path, remote):
        Process(["git", "remote", "set-url", remote, url], cwd=path).run()
        return
    Process(["git", "remote", "add", remote, url], cwd=path).run()


def git_branch_set_upstream(
    path: Path,
    branch: str,
    remote: str = "origin",
) -> None:
    """Set the upstream of a branch.

    Args:
        path (Path): Path to the repository.
        branch (str): Branch name.
        remote (str, optional): Remote name. Defaults to "origin".

    """
    Process(
        ["git", "branch", "--set-upstream-to", f"{remote}/{branch}", branch],
        cwd=path,
    ).run()


if __name__ == "__main__":
    import shutil
    import sys

    import colorama
    import rich

    from rubisco.lib.fileutil import (  # pylint: disable=ungrouped-imports
        TemporaryObject,
    )
    from rubisco.shared.ktrigger import bind_ktrigger_interface

    colorama.init()

    class _GitTestKTrigger(IKernelTrigger):
        def on_update_git_repo(
            self,
            *,
            path: Path,
            branch: str,
        ) -> None:
            rich.print(
                "[blue]=>[/blue] Updating Git repository "
                f"'[underline]{path}[/underline]'({branch}) ...",
            )

        def on_clone_git_repo(
            self,
            *,
            url: str,
            path: Path,
            branch: str,
        ) -> None:
            rich.print(
                f"[blue]=>[/blue] Cloing Git repository "
                f"{url} into "
                f"'[underline]{path}[/underline]'({branch}) ...",
            )

        def pre_speedtest(self, *, host: str) -> None:
            rich.print(
                f"[blue]=>[/blue] Testing speed for {host} ...",
                end="\n",
            )

        def post_speedtest(self, *, host: str, speed: int) -> None:
            speed_str = f"{speed} us" if speed != -1 else " - CANCELED"
            rich.print(f"[blue]::[/blue] Speed: {host} {speed_str}", end="\n")

        def pre_exec_process(self, *, proc: Process) -> None:
            rich.print(
                f"[blue]=>[/blue] Executing: [cyan]{proc.origin_cmd}[/cyan]",
            )
            sys.stdout.write(colorama.Fore.LIGHTBLACK_EX)
            sys.stdout.flush()

        def post_exec_process(
            self,
            *,
            proc: Process,  # noqa: ARG002
            retcode: int,
            raise_exc: bool,  # noqa: ARG002
        ) -> None:
            sys.stdout.write(colorama.Fore.RESET)
            sys.stdout.flush()
            if retcode != 0:
                rich.print(f"[red] Process failed with code {retcode}.[/red]")

    bind_ktrigger_interface("test", _GitTestKTrigger())

    # Test: Is a Git repository.
    git_repo = TemporaryObject.new_directory()
    non_git_repo = TemporaryObject.new_directory()
    Process(["git", "init"], cwd=git_repo.path).run()
    assert is_git_repo(git_repo.path) is True  # noqa: S101
    assert is_git_repo(non_git_repo.path) is False  # noqa: S101

    # Test: Clone a repository shallowly.
    git_clone(
        "cppp-project/cppp-reiconv@github",
        Path("cppp-reiconv"),
        branch="main",
        shallow=True,
    )

    # Test: Clone a existing repository without strict mode.
    git_clone(
        "/hello@savannah",
        Path("hello"),
        branch="master",
        shallow=True,
        strict=False,
    )

    # Test: Clone a existing repository with strict mode.
    try:
        git_clone(
            "/hello@savannah",
            Path("hello"),
            branch="master",
            shallow=True,
            strict=True,
        )
        _MSG = "Should raise a FileExistsError."
        raise AssertionError(_MSG)
    except FileExistsError:
        pass

    # Test: Update a repository.
    git_update(Path("hello"), branch="master")

    # Test: Update a non-existing repository.
    try:
        git_update(Path("libiconv"), branch="master")
        _MSG_ = "Should raise a FileNotFoundError."
        raise AssertionError(_MSG_)
    except FileNotFoundError:
        pass

    shutil.rmtree("hello")
    shutil.rmtree("cppp-reiconv")
    rich.print("[blue]=>[/blue] Done.")
