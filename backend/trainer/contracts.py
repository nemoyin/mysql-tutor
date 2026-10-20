from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class RuntimeState:
    phase: str
    mysql_port: int | None = None
    message: str = ''
    recoverable: bool = True


@dataclass
class ColumnMeta:
    name: str
    kind: str


@dataclass
class QueryResult:
    columns: list[ColumnMeta]
    rows: list[list[Any]]
    total_rows: int | None = None
    truncated: bool = False
    elapsed_ms: int = 0


@dataclass
class GradeResult:
    status: Literal['passed', 'incorrect', 'ungraded']
    reason: str


class QueryFailure(Exception):
    def __init__(self, code: str, original: str, explanation: str = '', mysql_errno: int | None = None):
        self.code, self.original, self.explanation, self.mysql_errno = code, original, explanation, mysql_errno
        super().__init__(explanation or original)

    def payload(self):
        return dict(code=self.code, original=self.original, explanation=self.explanation, mysql_errno=self.mysql_errno)
