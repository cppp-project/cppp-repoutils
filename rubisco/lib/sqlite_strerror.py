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

"""Return a string describing an SQLite error code."""

from sqlite3 import (
    SQLITE_ABORT,
    SQLITE_ABORT_ROLLBACK,
    SQLITE_AUTH,
    SQLITE_AUTH_USER,
    SQLITE_BUSY,
    SQLITE_BUSY_RECOVERY,
    SQLITE_BUSY_SNAPSHOT,
    SQLITE_BUSY_TIMEOUT,
    SQLITE_CANTOPEN,
    SQLITE_CANTOPEN_CONVPATH,
    SQLITE_CANTOPEN_DIRTYWAL,
    SQLITE_CANTOPEN_FULLPATH,
    SQLITE_CANTOPEN_ISDIR,
    SQLITE_CANTOPEN_NOTEMPDIR,
    SQLITE_CANTOPEN_SYMLINK,
    SQLITE_CONSTRAINT,
    SQLITE_CONSTRAINT_CHECK,
    SQLITE_CONSTRAINT_COMMITHOOK,
    SQLITE_CONSTRAINT_FOREIGNKEY,
    SQLITE_CONSTRAINT_FUNCTION,
    SQLITE_CONSTRAINT_NOTNULL,
    SQLITE_CONSTRAINT_PINNED,
    SQLITE_CONSTRAINT_PRIMARYKEY,
    SQLITE_CONSTRAINT_ROWID,
    SQLITE_CONSTRAINT_TRIGGER,
    SQLITE_CONSTRAINT_UNIQUE,
    SQLITE_CORRUPT,
    SQLITE_CORRUPT_INDEX,
    SQLITE_CORRUPT_SEQUENCE,
    SQLITE_CORRUPT_VTAB,
    SQLITE_DONE,
    SQLITE_EMPTY,
    SQLITE_ERROR,
    SQLITE_ERROR_MISSING_COLLSEQ,
    SQLITE_ERROR_SNAPSHOT,
    SQLITE_FORMAT,
    SQLITE_FULL,
    SQLITE_INTERNAL,
    SQLITE_INTERRUPT,
    SQLITE_IOERR,
    SQLITE_IOERR_ACCESS,
    SQLITE_IOERR_BEGIN_ATOMIC,
    SQLITE_IOERR_BLOCKED,
    SQLITE_IOERR_CHECKRESERVEDLOCK,
    SQLITE_IOERR_CLOSE,
    SQLITE_IOERR_COMMIT_ATOMIC,
    SQLITE_IOERR_CONVPATH,
    SQLITE_IOERR_CORRUPTFS,
    SQLITE_IOERR_DATA,
    SQLITE_IOERR_DELETE,
    SQLITE_IOERR_DELETE_NOENT,
    SQLITE_IOERR_DIR_CLOSE,
    SQLITE_IOERR_DIR_FSYNC,
    SQLITE_IOERR_FSTAT,
    SQLITE_IOERR_FSYNC,
    SQLITE_IOERR_GETTEMPPATH,
    SQLITE_IOERR_LOCK,
    SQLITE_IOERR_MMAP,
    SQLITE_IOERR_NOMEM,
    SQLITE_IOERR_RDLOCK,
    SQLITE_IOERR_READ,
    SQLITE_IOERR_ROLLBACK_ATOMIC,
    SQLITE_IOERR_SEEK,
    SQLITE_IOERR_SHMLOCK,
    SQLITE_IOERR_SHMMAP,
    SQLITE_IOERR_SHMOPEN,
    SQLITE_IOERR_SHMSIZE,
    SQLITE_IOERR_SHORT_READ,
    SQLITE_IOERR_TRUNCATE,
    SQLITE_IOERR_UNLOCK,
    SQLITE_IOERR_WRITE,
    SQLITE_LOCKED,
    SQLITE_LOCKED_SHAREDCACHE,
    SQLITE_LOCKED_VTAB,
    SQLITE_MISMATCH,
    SQLITE_MISUSE,
    SQLITE_NOLFS,
    SQLITE_NOMEM,
    SQLITE_NOTADB,
    SQLITE_NOTICE_RECOVER_WAL,
    SQLITE_PERM,
    SQLITE_PROTOCOL,
    SQLITE_RANGE,
    SQLITE_READONLY,
    SQLITE_READONLY_DBMOVED,
    SQLITE_READONLY_DIRECTORY,
    SQLITE_READONLY_RECOVERY,
    SQLITE_READONLY_ROLLBACK,
    SQLITE_ROW,
    SQLITE_SCHEMA,
    SQLITE_TOOBIG,
)

from rubisco.lib.l10n import _

__all__ = ["sqlite_strerror"]

SQLITE_OK = 0


def sqlite_strerror(  # noqa: C901 PLR0912 PLR0915 PLR0911 E501 RUF100 # pylint: disable=R0911 R0912 R0915
    errcode: int,
) -> str:
    """Return a string describing an SQLite error code.

    Args:
        errcode (int): The SQLite error code.

    Returns:
        str: A string describing the error code.

    """
    if errcode == SQLITE_OK:
        return _("Success.")
    if errcode == SQLITE_ERROR:
        return _("SQL error or missing database.")
    if errcode == SQLITE_INTERNAL:
        return _("Internal logic error in SQLite.")
    if errcode == SQLITE_PERM:
        return _("Access permission denied.")
    if errcode == SQLITE_ABORT:
        return _("Callback routine requested an abort.")
    if errcode == SQLITE_BUSY:
        return _("The database file is locked.")
    if errcode == SQLITE_LOCKED:
        return _("A table in the database is locked.")
    if errcode == SQLITE_NOMEM:
        return _("Memory allocation/reallocation failed.")
    if errcode == SQLITE_READONLY:
        return _("Attempt to write a readonly database.")
    if errcode == SQLITE_INTERRUPT:
        return _("Operation terminated by sqlite3_interrupt().")
    if errcode == SQLITE_IOERR:
        return _("I/O error.")
    if errcode == SQLITE_CORRUPT:
        return _("The database file has been corrupted.")
    if errcode == SQLITE_FULL:
        return _("Insertion failed because database is full.")
    if errcode == SQLITE_CANTOPEN:
        return _("Unable to open the database file.")
    if errcode == SQLITE_PROTOCOL:
        return _("Database file is malformed.")
    if errcode == SQLITE_EMPTY:
        # The SQLITE_EMPTY result code is not currently used.
        return "SQLITE_EMPTY is occurred."
    if errcode == SQLITE_SCHEMA:
        return _("The database schema changed.")
    if errcode == SQLITE_TOOBIG:
        return _("String or BLOB was too large.")
    if errcode == SQLITE_CONSTRAINT:
        return _("Abort due to constraint violation.")
    if errcode == SQLITE_MISMATCH:
        return _("Data type mismatch.")
    if errcode == SQLITE_MISUSE:
        return _("Library used incorrectly.")
    if errcode == SQLITE_NOLFS:
        return _("No large file support.")
    if errcode == SQLITE_AUTH:
        return _("Illegal authorization request.")
    if errcode == SQLITE_FORMAT:
        # The SQLITE_FORMAT result code is not currently used.
        return "SQLITE_FORMAT is occurred."
    if errcode == SQLITE_RANGE:
        return _("2nd parameter to sqlite3_bind out of range.")
    if errcode == SQLITE_NOTADB:
        return _("File opened that is not a database file.")
    if errcode == SQLITE_ROW:
        return _("Another row of output is available.")
    if errcode == SQLITE_DONE:
        return _("An operation is completed.")
    if errcode == SQLITE_ERROR_MISSING_COLLSEQ:
        return _(
            "An SQL statement could not be prepared because a collating "
            "sequence named in that SQL statement could not be located.",
        )
    if errcode == SQLITE_BUSY_RECOVERY:
        return _(
            "Operation could not continue because another process is busy"
            " recovering a WAL mode database file following a crash.",
        )
    if errcode == SQLITE_LOCKED_SHAREDCACHE:
        return _(
            "Access to an SQLite data record is blocked by another"
            " database connection that is using the same record in"
            " shared cache mode.",
        )
    if errcode == SQLITE_READONLY_RECOVERY:
        return _(
            "A WAL mode database cannot be opened because the database"
            " file needs to be recovered and recovery requires write"
            " access but only read access is available.",
        )
    if errcode == SQLITE_IOERR_READ:
        return _(
            "Hardware malfunction or a filesystem came unmounted while"
            " the file was open.",
        )
    if errcode == SQLITE_CORRUPT_VTAB:
        return _("Content in the virtual table is corrupt.")
    if errcode == SQLITE_CANTOPEN_NOTEMPDIR:
        # The SQLITE_CANTOPEN_NOTEMPDIR error code is no longer used.
        return "SQLITE_CANTOPEN_NOTEMPDIR is occurred."
    if errcode == SQLITE_CONSTRAINT_CHECK:
        return _("A CHECK constraint failed.")
    if errcode == SQLITE_AUTH_USER:
        return _(
            "An operation was attempted on a database for which the"
            " logged in user lacks sufficient authorization.",
        )
    if errcode == SQLITE_NOTICE_RECOVER_WAL:
        return _("A WAL mode database file has been recovered.")
    if errcode == SQLITE_ABORT_ROLLBACK:
        return _(
            "An SQL statement aborted because the transaction that was"
            " active when the SQL statement first started was rolled back.",
        )
    if errcode == SQLITE_BUSY_SNAPSHOT:
        return _(
            "A WAL mode database connection tries to promote a read "
            "transaction into a write transaction but finds that another "
            "database connection has already written to the database and "
            "thus invalidated prior reads.",
        )
    if errcode == SQLITE_LOCKED_VTAB:
        return _(
            "Virtual table implementations cannot complete the current"
            " operation because of locks held by other threads or processes.",
        )
    if errcode == SQLITE_READONLY_ROLLBACK:
        return _(
            "SQLite is unable to obtain a read lock on a WAL mode database "
            "because the shared-memory file associated with that database "
            "is read-only.",
        )
    if errcode == SQLITE_IOERR_SHORT_READ:
        return _(
            "A read attempt in the VFS layer was unable to obtain as many"
            " bytes as was requested.",
        )
    if errcode == SQLITE_CORRUPT_SEQUENCE:
        return _("The schema of the sqlite_sequence table is corrupt.")
    if errcode == SQLITE_CANTOPEN_ISDIR:
        return _(
            "A file failed to open because the file is really a directory.",
        )
    if errcode == SQLITE_CONSTRAINT_COMMITHOOK:
        return _(
            "A commit hook callback returned non-zero that thus caused"
            " the SQL statement to be rolled back.",
        )
    if errcode == SQLITE_ERROR_SNAPSHOT:
        return _("The historical snapshot is no longer available.")
    if errcode == SQLITE_BUSY_TIMEOUT:
        return _(
            "A blocking POSIX advisory file lock request in the VFS layer"
            " failed due to a timeout.",
        )
    if errcode == SQLITE_READONLY_ROLLBACK:
        return _(
            "A database cannot be opened because it has a hot journal "
            "that needs to be rolled back but cannot because the "
            "database is readonly.",
        )
    if errcode == SQLITE_IOERR_WRITE:
        return _(
            "An I/O error occured in the VFS layer while trying to "
            "write into a file on disk.",
        )
    if errcode == SQLITE_CORRUPT_INDEX:
        return _("SQLite detected an entry is or was missing from an index.")
    if errcode == SQLITE_CANTOPEN_FULLPATH:
        return _(
            "A file open operation failed because the operating system "
            "was unable to convert the filename into a full pathname.",
        )
    if errcode == SQLITE_CONSTRAINT_FOREIGNKEY:
        return _("A foreign key constraint failed.")
    if errcode == SQLITE_READONLY_DBMOVED:
        return _(
            "A database cannot be modified because the database file has "
            "been moved since it was opened.",
        )
    if errcode == SQLITE_IOERR_FSYNC:
        return _(
            "An I/O error occured in the VFS layer while trying to fsync.",
        )
    if errcode == SQLITE_CANTOPEN_CONVPATH:
        return _("cygwin_conv_path() failed.")
    if errcode == SQLITE_CONSTRAINT_FUNCTION:
        return _("A function constraint failed.")
    if errcode == SQLITE_IOERR_DIR_FSYNC:
        return _(
            "An I/O error occured in the VFS layer while trying to fsync.",
        )
    if errcode == SQLITE_CANTOPEN_DIRTYWAL:
        # The SQLITE_CANTOPEN_DIRTYWAL error code is not currently used.
        return "SQLITE_CANTOPEN_DIRTYWAL is occurred."
    if errcode == SQLITE_CONSTRAINT_NOTNULL:
        return _("A NOT NULL constraint failed.")
    if errcode == SQLITE_READONLY_DIRECTORY:
        return _(
            "The database is read-only because process does not have"
            " permission to create a journal file in the same directory"
            " as the database and the creation of a journal file is a "
            "prerequisite for writing.",
        )
    if errcode == SQLITE_IOERR_TRUNCATE:
        return _(
            "I/O error in the VFS layer while trying to truncate a"
            " file to a smaller size.",
        )
    if errcode == SQLITE_CANTOPEN_SYMLINK:
        return _(
            "SQLITE_OPEN_NOFOLLOW is used but the database file is a symlink.",
        )
    if errcode == SQLITE_CONSTRAINT_PRIMARYKEY:
        return _("A PRIMARY KEY constraint failed.")
    if errcode == SQLITE_IOERR_FSTAT:
        return _(
            "An I/O error occured in the VFS layer while trying to invoke "
            "fstat() (or the equivalent) on a file in order to determine "
            "information such as the file size or access permissions.",
        )
    if errcode == SQLITE_CONSTRAINT_TRIGGER:
        return _(
            "A RAISE function within a trigger fired, causing the SQL"
            " statement to abort.",
        )
    if errcode == SQLITE_IOERR_UNLOCK:
        return _(
            "An I/O error within xUnlock method on the "  # Extended IOERR.
            "sqlite3_io_methods object.",
        )
    if errcode == SQLITE_CONSTRAINT_UNIQUE:
        return _("A UNIQUE constraint failed.")
    if errcode == SQLITE_IOERR_RDLOCK:
        return _(
            "I/O error within xLock method on the sqlite3_io_methods"
            " object while trying to obtain a read lock.",
        )
    if errcode == SQLITE_IOERR_DELETE:
        return _("I/O error within xDelete method on the sqlite3_vfs object.")
    if errcode == SQLITE_CONSTRAINT_ROWID:
        return _("A rowid is not unique.")
    if errcode == SQLITE_IOERR_BLOCKED:
        # The SQLITE_IOERR_BLOCKED error code is no longer used.
        return "SQLITE_IOERR_BLOCKED is occurred."
    if errcode == SQLITE_CONSTRAINT_PINNED:
        return _(
            "An UPDATE trigger attempted do delete the row that was being"
            " updated in the middle of the update.",
        )
    if errcode == SQLITE_IOERR_NOMEM:
        return _(
            "An operation could not be completed due to the inability to "
            "allocate sufficient memory.",
        )
    if errcode == SQLITE_IOERR_ACCESS:
        return _(
            "I/O error occured within the xAccess "  # Extended IOERR.
            "method on the sqlite3_vfs object.",
        )
    if errcode == SQLITE_IOERR_CHECKRESERVEDLOCK:
        return _(
            "I/O error within the xCheckReservedLock method on the"
            " sqlite3_io_methods object.",
        )
    if errcode == SQLITE_IOERR_LOCK:
        return _("I/O error in the advisory file locking logic.")
    if errcode == SQLITE_IOERR_CLOSE:
        return _(
            "I/O error within the xClose method on the"  # Extended IOERR.
            " sqlite3_io_methods object.",
        )
    if errcode == SQLITE_IOERR_DIR_CLOSE:
        # The SQLITE_IOERR_DIR_CLOSE error code is no longer used.
        return "SQLITE_IOERR_DIR_CLOSE is occurred."
    if errcode == SQLITE_IOERR_SHMOPEN:
        return _(
            "I/O error within the xShmMap method on the"
            " sqlite3_io_methods object while trying to open"
            " a new shared memory segment.",
        )
    if errcode == SQLITE_IOERR_SHMSIZE:
        return _(
            "I/O error within the xShmMap method on the sqlite3_io_methods "
            'object while trying to enlarge a "shm" file as part of WAL mode '
            "transaction processing. This error may indicate that the "
            "underlying filesystem volume is out of space.",
        )
    if errcode == SQLITE_IOERR_SHMLOCK:
        # The SQLITE_IOERR_SHMLOCK error code is no longer used.
        return "SQLITE_IOERR_SHMLOCK is occurred."
    if errcode == SQLITE_IOERR_SHMMAP:
        return _(
            "I/O error within the xShmMap method on the "
            "sqlite3_io_methods object while trying to map a shared "
            "memory segment into the process address space.",
        )
    if errcode == SQLITE_IOERR_SEEK:
        return _(
            "I/O error within the xRead or xWrite methods on the "
            "sqlite3_io_methods object while trying to seek a file "
            "descriptor to the beginning point of the file where the"
            " read or write is to occur.",
        )
    if errcode == SQLITE_IOERR_DELETE_NOENT:
        return _(
            "The xDelete method on the sqlite3_vfs object failed because"
            " the file being deleted does not exist.",
        )
    if errcode == SQLITE_IOERR_MMAP:
        return _(
            "I/O error within the xFetch or xUnfetch methods on the"
            " sqlite3_io_methods object while trying to map or unmap"
            " part of the database file into the process address space.",
        )
    if errcode == SQLITE_IOERR_GETTEMPPATH:
        return _(
            "The VFS is unable to determine a suitable directory in which"
            " to place temporary files.",
        )
    if errcode == SQLITE_IOERR_CONVPATH:  # 6666
        return _("The cygwin_conv_path() system call failed.")
    if errcode == SQLITE_IOERR_BEGIN_ATOMIC:
        return _(
            "The underlying operating system reported and error on the"
            " SQLITE_FCNTL_BEGIN_ATOMIC_WRITE file-control.",
        )
    if errcode == SQLITE_IOERR_COMMIT_ATOMIC:
        return _(
            "The underlying operating system reported and error on the"
            " SQLITE_FCNTL_COMMIT_ATOMIC_WRITE file-control.",
        )
    if errcode == SQLITE_IOERR_ROLLBACK_ATOMIC:
        return _(
            "The underlying operating system reported and error on the"
            " SQLITE_FCNTL_ROLLBACK_ATOMIC_WRITE file-control.",
        )
    if errcode == SQLITE_IOERR_DATA:
        return _("The checksum on a page of the database file is incorrect.")
    if errcode == SQLITE_IOERR_CORRUPTFS:
        return _(
            "A seek or read failure was due to the request not falling"
            " within the file's boundary rather than an ordinary device"
            " failure.",
        )
    return _("Unknown error code.")
