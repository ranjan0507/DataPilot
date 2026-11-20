from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_ROWS_STORED = 100_000
PREVIEW_ROWS = 10
OUTPUT_CHARACTERS = 20_000
MAX_PREVIEW_COLUMNS = 100
MAX_PREVIEW_CELL_CHARS = 20_000


class ErrorCode(StrEnum):
    REJECTED_SQL = "REJECTED_SQL"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str


class ResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = "1"
    ok: bool
    data: Any | None = None
    error: ErrorDetail | None = None


class Column(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    type: str = Field(max_length=100)


class Preview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[dict[str, Any]] = Field(max_length=PREVIEW_ROWS)
    truncated: bool

    @field_validator("rows")
    @classmethod
    def enforce_preview_limits(
        cls,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        for row in rows:
            if len(row) > MAX_PREVIEW_COLUMNS:
                msg = f"A preview row has more than {MAX_PREVIEW_COLUMNS} columns"
                raise ValueError(msg)
            for name, value in row.items():
                if len(name) > 200:
                    msg = "A preview column name exceeds 200 characters"
                    raise ValueError(msg)
                pending = [value]
                while pending:
                    item = pending.pop()
                    if isinstance(item, str) and len(item) > MAX_PREVIEW_CELL_CHARS:
                        msg = f"A preview cell exceeds {MAX_PREVIEW_CELL_CHARS} characters"
                        raise ValueError(msg)
                    if isinstance(item, dict):
                        pending.extend(item.values())
                    elif isinstance(item, list):
                        pending.extend(item)
        return rows


class ResultRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: UUID
    columns: list[Column] = Field(max_length=MAX_PREVIEW_COLUMNS)
    row_count: int
    preview: Preview
