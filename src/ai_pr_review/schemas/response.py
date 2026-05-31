from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    message: str
    data: DataT | None = None
    error: str | dict[str, Any] | None = None
