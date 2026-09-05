"""The one exception type, carrying the exit code and the fixing command."""

USAGE = 2
UNKNOWN_HOST = 3
OFFLINE = 4
REMOTE_FAILED = 5
PREREQ = 6
INVITE = 7
RESIDUE = 8


class CsyncError(Exception):
    def __init__(self, code, message, fix=None, data=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fix = fix
        self.data = data or {}
