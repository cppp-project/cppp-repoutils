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

"""Package management utils for environment."""

import os
import sqlite3
import sys
import threading
import time
import venv
from pathlib import Path
from types import TracebackType
from typing import Self

from rubisco.config import (
    DB_FILENAME,
    DEFAULT_CHARSET,
    EXTENSIONS_DIR,
    GLOBAL_EXTENSIONS_VENV_DIR,
    USER_EXTENSIONS_VENV_DIR,
    VENV_LOCK_FILENAME,
    WORKSPACE_EXTENSIONS_VENV_DIR,
)
from rubisco.envutils.env_db import RUEnvDB
from rubisco.envutils.env_type import EnvType
from rubisco.envutils.utils import add_venv_to_syspath, is_venv
from rubisco.lib.exceptions import RUError, RUOSError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.process import is_valid_pid
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = [
    "GLOBAL_ENV",
    "USER_ENV",
    "WORKSPACE_ENV",
    "RUEnvironment",
]


_CREATE_DB_SQL = """
CREATE TABLE extensions (
    name VARCHAR(64) PRIMARY KEY,
    version VARCHAR(64) NOT NULL,
    description TEXT,
    homepage TEXT,
    maintainers TEXT,
    license TEXT,
    tags TEXT,
    requirements TEXT
)
"""


def _check_vaild_db(db_file: Path) -> bool:
    try:
        db_connection = sqlite3.connect(db_file)
        db_cursor = db_connection.cursor()
        db_cursor.execute("SELECT * FROM extensions").close()
        db_connection.close()
        # Else block is low readability.
        return True  # noqa: TRY300
    except sqlite3.Error:
        return False


class RUEnvironment:
    """Extension environment manager."""

    _path: Path
    _type: EnvType
    _lockfile: Path
    db_file: Path
    db_handle: RUEnvDB

    def __init__(self, path: Path, env_type: EnvType) -> None:
        """Initialize the environment manager."""
        self._path = path
        self._type = env_type
        self._lockfile = self.path / VENV_LOCK_FILENAME
        self.db_file = self.path / DB_FILENAME
        self.db_handle = RUEnvDB(self.db_file, env_type)

    def __str__(self) -> str:
        """Get the string representation of the environment."""
        return f"RUEnvironment({self.path}, {self.env_type})"

    def create(self) -> None:
        """Create the environment if not exists. Check it if exists.

        Raises:
            RUError: If failed to create the venv or the database.
            RUOSError: If OS error occurred.

        """
        if self.exists() and not self.db_is_valid():
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _("The database ${{path}} is broken."),
                    fmt={"path": make_pretty(self.db_file)},
                ),
            )
        if self.path.exists() and not self.valid():
            logger.error("The environment '%s' is broken.", self.path)
            raise RUError(
                _("Failed to check the environment."),
                hint=fast_format_str(
                    _(
                        "The ${{path}} is not a valid venv but exists."
                        "Please remove it and try again.",
                    ),
                    fmt={"path": make_pretty(self.path)},
                ),
            )
        if not self.path.exists():
            logger.info("Setting up a new venv: '%s'", self.path)
            call_ktrigger(IKernelTrigger.on_create_venv, path=self.path)
            try:
                venv.create(self.path, with_pip=True, upgrade_deps=True)
                (self.path / EXTENSIONS_DIR).mkdir(exist_ok=True, parents=True)
                logger.debug("Creating database %s", self.db_file)
                with sqlite3.connect(self.db_file) as db_connection:
                    db_connection.execute(_CREATE_DB_SQL)
                    db_connection.commit()
                add_venv_to_syspath(self.path)
            except OSError as exc:
                raise RUOSError(
                    exc,
                    hint=_(
                        "Failed to create venv. Consider to check the"
                        "permissions of the path.",
                    ),
                ) from exc
            except sqlite3.Error as exc:
                raise RUError(
                    exc,
                    hint=_(
                        "Failed to create the database for the environment.",
                    ),
                ) from exc

    @property
    def path(self) -> Path:
        """Get the path of the environment."""
        return self._path

    @property
    def extensions_venv_path(self) -> Path:
        """Get the path of the extensions venv."""
        return self.path / EXTENSIONS_DIR

    @property
    def env_type(self) -> EnvType:
        """Get the type of the environment."""
        return self._type

    def is_global(self) -> bool:
        """Check if the environment is global."""
        return self.env_type == EnvType.GLOBAL

    def is_user(self) -> bool:
        """Check if the environment is user."""
        return self.env_type == EnvType.USER

    def is_workspace(self) -> bool:
        """Check if the environment is workspace."""
        return self.env_type == EnvType.WORKSPACE

    def is_locked(self) -> bool:
        """Check if the environment is locked."""
        return self._lockfile.exists()

    def is_locked_by_self(self) -> bool:
        """Check if the environment is locked by the current thread."""
        if not self.is_locked():
            return False

        lock_pid, lock_thread_id, _rc = self._parse_lockfile()
        is_current_thread = lock_thread_id == threading.get_ident()
        is_current_thread &= lock_pid == os.getpid()

        return is_current_thread

    def _wait_lock(self) -> bool:
        logger.info(
            "Waiting for the environment to be unlocked ('%s')",
            self._lockfile,
        )
        msg = _(
            "Waiting for the environment to be unlocked "
            "(${{path}}): ${{seconds}} seconds.",
        )
        wait_time = 0
        locked = False
        while self.is_locked() and not self.is_locked_by_self():
            locked = True
            call_ktrigger(
                IKernelTrigger.on_wait,
                msg=fast_format_str(
                    msg,
                    fmt={
                        "path": make_pretty(self._lockfile),
                        "seconds": wait_time,
                    },
                ),
                cur_time=wait_time,
            )
            time.sleep(1)
            wait_time += 1

        return locked

    def _check_alerady_locked(
        self,
        lock_pid: int,
        lock_thread_id: int,
    ) -> bool:
        is_current_thread = lock_thread_id == threading.get_ident()
        is_current_thread &= lock_pid == os.getpid()

        if not is_current_thread:  # Skip waiting if the current thread.
            logger.warning(
                "The environment '%s' is already locked by PID %d, "
                "thread %d, If you want to force unlock it, please remove "
                "the lock file '%s' manually.",
                self.path,
                lock_thread_id,
                lock_pid,
                self._lockfile,
            )
            str_pid = str(_("Unknown") if lock_pid == -1 else lock_pid)
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _(
                        "The environment ${{path}} is already locked by PID "
                        "${{pid}}. If you want to force unlock it, please "
                        "remove the lock file ${{lockfile}} manually.",
                    ),
                    fmt={
                        "path": make_pretty(self.path),
                        "pid": str_pid,
                        "lockfile": make_pretty(self._lockfile),
                    },
                ),
            )
            if lock_pid != -1 and not is_valid_pid(lock_pid):
                call_ktrigger(  # If the process has already exited, warn.
                    IKernelTrigger.on_warning,
                    message=fast_format_str(
                        _(
                            "The PID '${{pid}}' is not valid. Maybe the "
                            "process has already exited. "
                            "Remove the lock file if you believe the "
                            "process has already exited.",
                        ),
                        fmt={
                            "pid": str(lock_pid),
                        },
                    ),
                )

            return self._wait_lock()
        return False

    def _parse_lockfile(self) -> tuple[int, int, int]:
        pid = -1
        thread_id = -1
        ref_count = 0
        try:
            with self._lockfile.open(encoding=DEFAULT_CHARSET) as f:
                pid = int(f.readline().strip())
                thread_id = int(f.readline().strip())
                ref_count = int(f.readline().strip())
        except ValueError:
            logger.warning(
                "The lock file '%s' is broken.",
                self._lockfile,
            )
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _(
                        "The lock file ${{path}} is broken.",
                    ),
                    fmt={"path": make_pretty(self._lockfile)},
                ),
            )
        except OSError as exc:
            logger.exception(
                "Failed to read the lock file '%s'.",
                self._lockfile,
            )
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=fast_format_str(
                    _(
                        "Failed to read the lock file ${{path}}: ${{msg}}",
                    ),
                    fmt={"path": make_pretty(self._lockfile), "msg": str(exc)},
                ),
            )

        return pid, thread_id, ref_count

    def _update_lock(self, pid: int, thread_id: int, ref_count: int) -> None:
        with self._lockfile.open(
            "w",
            encoding=DEFAULT_CHARSET,
        ) as f:
            f.write(f"{pid}\n{thread_id}\n{ref_count}\n")

    def lock(self) -> None:
        """Lock the environment."""
        self.create()  # Ensure the environment is created.

        ref_count = 0
        if self.is_locked():
            lock_pid, lock_thread_id, ref_count = self._parse_lockfile()
            if self._check_alerady_locked(lock_pid, lock_thread_id):
                ref_count = 0  # Reset the refcount if another unlocked.

        ref_count += 1
        this_pid = os.getpid()
        this_thread_id = threading.get_ident()
        logger.info(
            "Locking the environment '%s' with PID %d, thread %d, "
            "with %d refence count.",
            self.path,
            this_pid,
            this_thread_id,
            ref_count,
        )
        self._update_lock(this_pid, this_thread_id, ref_count)

    def unlock(self) -> None:
        """Unlock the environment."""
        if self.is_locked():
            logger.info("Unlocking the environment '%s'.", self.path)
            try:
                pid, thread_id, ref_count = self._parse_lockfile()
                if self.is_locked_by_self() and ref_count > 1:
                    ref_count -= 1
                    self._update_lock(pid, thread_id, ref_count)
                elif self.is_locked_by_self():
                    self._lockfile.unlink()
                else:
                    logger.warning(
                        "The environment '%s' is locked by another thread.",
                        self.path,
                    )
                    call_ktrigger(
                        IKernelTrigger.on_warning,
                        message=fast_format_str(
                            _(
                                "The environment ${{path}} is locked by "
                                "another thread (PID ${{pid}}, Thread "
                                "${{thread}}). Unlock request is ignored.",
                            ),
                            fmt={
                                "path": make_pretty(self.path),
                                "pid": str(pid),
                                "thread": str(thread_id),
                            },
                        ),
                    )
            except OSError as exc:
                logger.exception(
                    "Failed to unlock the environment '%s'.",
                    self.path,
                )
                call_ktrigger(
                    IKernelTrigger.on_warning,
                    message=fast_format_str(
                        _(
                            "Failed to unlock the extension environment "
                            "${{path}}: ${{msg}}",
                        ),
                        fmt={"path": make_pretty(self.path), "msg": str(exc)},
                    ),
                )
        else:
            logger.warning("The environment '%s' is not locked.", self.path)

    def __enter__(self) -> Self:
        """Lock the environment."""
        self.lock()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Unlock the environment."""
        self.unlock()

    def add_to_path(self) -> None:
        """Add the environment to the system path."""
        add_venv_to_syspath(self.path)

    def exists(self) -> bool:
        """Check if the database exists."""
        return is_venv(self.path) and self.db_file.exists()

    def db_is_valid(self) -> bool:
        """Check if the database is valid."""
        return _check_vaild_db(self.db_file)

    def valid(self) -> bool:
        """Check if the environment is valid."""
        return is_venv(self.path) and self.db_is_valid()


GLOBAL_ENV = RUEnvironment(GLOBAL_EXTENSIONS_VENV_DIR, EnvType.GLOBAL)
USER_ENV = RUEnvironment(USER_EXTENSIONS_VENV_DIR, EnvType.USER)
WORKSPACE_ENV = RUEnvironment(WORKSPACE_EXTENSIONS_VENV_DIR, EnvType.WORKSPACE)

GLOBAL_ENV.add_to_path()
USER_ENV.add_to_path()
WORKSPACE_ENV.add_to_path()


if __name__ == "__main__":
    import rubisco.cli.output
    import rubisco.shared.ktrigger

    class _InstallTrigger(IKernelTrigger):
        def on_create_venv(self, *, path: Path) -> None:
            rubisco.cli.output.output_step(
                "Creating Rubisco extension environment:"
                f" '{make_pretty(path.absolute())}' ...",
            )

    rubisco.shared.ktrigger.bind_ktrigger_interface(
        "installer",
        _InstallTrigger(),
    )

    if "--setup-global-env" in sys.argv:
        try:
            GLOBAL_ENV.create()
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup global environment.")
            rubisco.cli.output.show_exception(exc_)
    elif "--setup-user-env" in sys.argv:
        try:
            USER_ENV.create()
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup user environment.")
            rubisco.cli.output.show_exception(exc_)
    elif "--setup-workspace-env" in sys.argv:
        try:
            WORKSPACE_ENV.create()
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup workspace environment.")
            rubisco.cli.output.show_exception(exc_)
